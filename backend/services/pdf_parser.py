import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from all pages of a PDF."""
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        pages.append(f"[Page {i + 1}]\n{text}")
    doc.close()
    return "\n\n".join(pages)


async def parse_and_store_cv(pdf_path: str, db) -> None:
    """Extract text from CV PDF, send to Claude for structuring, save to profile."""
    from backend.models.db_models import Profile
    from backend.services.claude_service import parse_cv_to_profile

    raw_text = extract_text_from_pdf(pdf_path)
    structured = await parse_cv_to_profile(raw_text)

    profile = db.get(Profile, 1)
    if not profile:
        profile = Profile(id=1)
        db.add(profile)

    for field, value in structured.items():
        if hasattr(profile, field) and value is not None:
            setattr(profile, field, value)

    profile.cv_file_path = pdf_path
    db.commit()
