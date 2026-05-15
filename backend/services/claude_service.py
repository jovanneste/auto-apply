"""
Claude service — drives all AI calls through the Claude Code CLI (`claude -p`).
No Anthropic API key required; uses your existing Claude Code authentication.
"""
import json
import asyncio
import shutil
from typing import AsyncGenerator, Any


CLAUDE_BIN = shutil.which("claude") or "claude"


async def _run_claude(prompt: str, system: str = "", max_wait: int = 120) -> str:
    """Run `claude -p` non-interactively and return the text response."""
    cmd = [CLAUDE_BIN, "-p", "--output-format", "text", "--dangerously-skip-permissions"]
    if system:
        cmd += ["--system-prompt", system]
    cmd.append(prompt)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=max_wait)
    text = stdout.decode().strip()
    if proc.returncode != 0 and not text:
        raise RuntimeError(f"Claude CLI error: {stderr.decode().strip()}")
    return text


async def _stream_claude(prompt: str, system: str = "") -> AsyncGenerator[str, None]:
    """Run `claude -p` with stream-json output, yield text chunks as they arrive."""
    cmd = [
        CLAUDE_BIN, "-p",
        "--output-format", "stream-json",
        "--include-partial-messages",
        "--dangerously-skip-permissions",
    ]
    if system:
        cmd += ["--system-prompt", system]
    cmd.append(prompt)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    assert proc.stdout is not None
    async for raw_line in proc.stdout:
        line = raw_line.decode().strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Partial assistant text chunks
        if event.get("type") == "assistant" and event.get("message"):
            msg = event["message"]
            for block in msg.get("content", []):
                if block.get("type") == "text":
                    yield block["text"]

    await proc.wait()


def _strip_fences(text: str) -> str:
    """Remove markdown code fences that Claude sometimes wraps JSON in."""
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) >= 2 else text
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def _build_profile_context(profile, qa_pairs) -> str:
    parts = ["=== APPLICANT PROFILE ==="]
    for col in ["full_name", "email", "phone", "address", "linkedin", "website",
                "summary", "species_expertise", "field_sites",
                "conservation_philosophy", "teaching_experience"]:
        val = getattr(profile, col, None)
        if val:
            parts.append(f"{col}: {val}")
    for json_col in ["education_json", "work_history_json", "skills_json",
                     "publications_json", "grants_json", "awards_json", "fieldwork_json"]:
        val = getattr(profile, json_col, None)
        if val:
            parts.append(f"\n{json_col}:\n{val}")
    if qa_pairs:
        parts.append("\n=== COMMON Q&A PAIRS ===")
        for qa in qa_pairs:
            parts.append(f"Q: {qa.question}\nA: {qa.answer}")
    return "\n".join(parts)


# ── CV Parsing ────────────────────────────────────────────────────────────────

CV_PARSE_SYSTEM = """You are helping extract structured professional information from a wildlife biologist's CV.
Return ONLY a valid JSON object with these exact keys (use null for missing fields, never invent data):

{
  "full_name": string,
  "email": string,
  "phone": string,
  "address": string,
  "linkedin": string,
  "website": string,
  "summary": string,
  "education_json": "[{\"degree\": str, \"field\": str, \"institution\": str, \"year\": str, \"gpa\": str}]",
  "work_history_json": "[{\"title\": str, \"org\": str, \"start\": str, \"end\": str, \"description\": str}]",
  "skills_json": "[str, ...]",
  "publications_json": "[{\"title\": str, \"journal\": str, \"year\": str, \"doi\": str, \"authors\": str}]",
  "grants_json": "[{\"title\": str, \"agency\": str, \"amount\": str, \"year\": str, \"role\": str}]",
  "awards_json": "[{\"name\": str, \"issuer\": str, \"year\": str}]",
  "fieldwork_json": "[{\"location\": str, \"species\": str, \"methods\": str, \"years\": str}]",
  "species_expertise": "comma-separated list of species/taxa",
  "field_sites": "comma-separated list of field sites/regions",
  "conservation_philosophy": "brief statement derived from CV content",
  "teaching_experience": "summary of teaching roles"
}

All *_json values must be valid JSON strings (stringify arrays). Return ONLY the JSON object, no markdown."""


async def parse_cv_to_profile(raw_cv_text: str) -> dict[str, Any]:
    prompt = f"Extract structured data from this CV:\n\n{raw_cv_text}"
    text = await _run_claude(prompt, system=CV_PARSE_SYSTEM, max_wait=120)
    return json.loads(_strip_fences(text))


# ── Field Mapping ─────────────────────────────────────────────────────────────

FIELD_MAPPING_SYSTEM = """You are helping a wildlife biologist fill out online job application forms.
You have access to her complete professional profile. For each form field, propose the best answer.

Rules:
- Use only information from the profile. Do not invent data.
- For salary, references, start date, and personal statements not derivable from the profile: set confidence to "missing".
- For select/radio fields, proposed_answer must be the exact option value from options_json, not free text.
- For file upload fields: set proposed_answer to "[Upload CV]" and confidence to "high".
- Keep answers concise unless the field type is textarea (then be thorough and professional).
- For cover letters: write a tailored, professional letter using the job context and her profile.

Return ONLY a JSON array, one object per field, in the same order as input:
[
  {
    "proposed_answer": string or null,
    "confidence": "high" | "medium" | "low" | "missing",
    "reasoning": "one sentence",
    "source": "profile" | "qa_pair" | "inferred" | "missing"
  },
  ...
]"""


async def map_fields_to_profile(
    fields: list[dict],
    profile,
    qa_pairs: list,
    job_title: str,
    organization: str,
    ats_type: str,
) -> list[dict]:
    profile_context = _build_profile_context(profile, qa_pairs)

    fields_text = json.dumps([
        {
            "index": i,
            "field_type": f.get("field_type"),
            "field_label": f.get("field_label"),
            "field_name": f.get("field_name"),
            "field_placeholder": f.get("field_placeholder"),
            "is_required": f.get("is_required"),
            "options_json": f.get("options_json"),
        }
        for i, f in enumerate(fields)
    ], indent=2)

    prompt = (
        f"{profile_context}\n\n"
        f"Job: {job_title} at {organization} (ATS: {ats_type})\n\n"
        f"Please fill out these form fields:\n{fields_text}"
    )

    text = await _run_claude(prompt, system=FIELD_MAPPING_SYSTEM, max_wait=180)
    result = json.loads(_strip_fences(text))

    while len(result) < len(fields):
        result.append({
            "proposed_answer": None,
            "confidence": "missing",
            "reasoning": "Not returned by Claude",
            "source": "missing",
        })

    return result[:len(fields)]


# ── Instruction Generation ────────────────────────────────────────────────────

INSTRUCTION_SYSTEM = """You are generating step-by-step form-filling instructions for a wildlife biologist applying for a job.
Write clear, numbered instructions organized by form page. Use this format:

## Step 1: Open the Application
1. Go to [URL]
2. Click "Apply Now" (or similar button)

## Step 2: [Section Name] (Page 1 of N)
3. In the "[Field Label]" field, type: [answer]
   (or: select: / choose: / check: for non-text fields)
...

## Upload Documents
N. Click the "[Upload button label]" button and select your CV file.

## Final Step: Review and Submit
N. Review all your answers carefully.
N+1. Click the Submit button.

Important notes:
- Do NOT use the browser Back button — it may reset your answers.
- If a field is marked NEEDS YOUR INPUT, fill it in yourself before submitting.

Be specific and complete. Include every field."""


async def generate_instructions_stream(job) -> AsyncGenerator[str, None]:
    fields_by_page: dict[int, list] = {}
    for f in job.fields:
        page = f.page_number or 1
        fields_by_page.setdefault(page, []).append(f)

    pages_text_parts = []
    for page_num in sorted(fields_by_page):
        pages_text_parts.append(f"\n### Page {page_num}")
        for f in fields_by_page[page_num]:
            answer = f.final_answer or f.proposed_answer or "(NEEDS YOUR INPUT)"
            flag = " NEEDS YOUR INPUT" if not (f.final_answer or f.proposed_answer) else ""
            pages_text_parts.append(
                f"- [{f.field_type}] {f.field_label or f.field_name or 'Unknown field'}"
                f" (required: {f.is_required}): {answer}{flag}"
            )

    total_pages = max(fields_by_page.keys()) if fields_by_page else 1
    prompt = (
        f"Job URL: {job.url}\n"
        f"Job Title: {job.title or 'Unknown'}\n"
        f"Organization: {job.organization or 'Unknown'}\n"
        f"ATS Type: {job.ats_type or 'generic'}\n"
        f"Total form pages: {total_pages}\n\n"
        f"Form fields to fill:\n" + "\n".join(pages_text_parts)
    )

    async for chunk in _stream_claude(prompt, system=INSTRUCTION_SYSTEM):
        yield chunk
