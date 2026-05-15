import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.db_models import Job, FormField
from backend.models.schemas import FieldUpdate, FormFieldResponse
from backend.utils.streaming import sse_event, sse_stream

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# Maps job_id → asyncio.Queue for SSE events
_queues: dict[int, asyncio.Queue] = {}

# Maps job_id → asyncio.Event for "user pressed Continue"
_continue_events: dict[int, asyncio.Event] = {}


def get_queue(job_id: int) -> asyncio.Queue:
    if job_id not in _queues:
        _queues[job_id] = asyncio.Queue()
    return _queues[job_id]


def get_continue_event(job_id: int) -> asyncio.Event:
    if job_id not in _continue_events:
        _continue_events[job_id] = asyncio.Event()
    return _continue_events[job_id]


@router.post("/{job_id}/start")
async def start_analysis(job_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status == "analyzing":
        raise HTTPException(status_code=409, detail="Analysis already running")

    job.status = "analyzing"
    db.commit()

    queue = get_queue(job_id)
    continue_event = get_continue_event(job_id)
    continue_event.clear()

    background_tasks.add_task(_run_analysis, job_id, queue, continue_event)
    return {"status": "started", "job_id": job_id}


@router.get("/{job_id}/stream")
async def stream_analysis(job_id: int):
    queue = get_queue(job_id)

    async def event_generator():
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30)
                yield event
                if '"type": "complete"' in event or '"type": "error"' in event:
                    break
            except asyncio.TimeoutError:
                yield sse_event("ping")

    return StreamingResponse(
        sse_stream(event_generator()),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{job_id}/continue")
async def continue_analysis(job_id: int):
    event = get_continue_event(job_id)
    event.set()
    return {"status": "resumed"}


@router.put("/{job_id}/fields/{field_id}", response_model=FormFieldResponse)
def update_field(job_id: int, field_id: int, data: FieldUpdate, db: Session = Depends(get_db)):
    field = db.get(FormField, field_id)
    if not field or field.job_id != job_id:
        raise HTTPException(status_code=404, detail="Field not found")
    field.final_answer = data.final_answer
    field.user_edited = True
    db.commit()
    db.refresh(field)
    return field


async def _run_analysis(job_id: int, queue: asyncio.Queue, continue_event: asyncio.Event):
    """Background task: scrape → extract fields → map with Claude → save."""
    from backend.database import SessionLocal
    from backend.services.scraper import scrape_job
    from backend.services.claude_service import map_fields_to_profile

    db = SessionLocal()
    try:
        job = db.get(Job, job_id)

        async def emit(event_type: str, **kwargs):
            await queue.put(sse_event(event_type, **kwargs))

        await emit("status", message="Opening browser...")

        result = await scrape_job(job.url, queue, continue_event)

        if result is None:
            job.status = "needs_input"
            db.commit()
            return

        fields_data, screenshot_path, ats_type, job_title, organization = result

        job.ats_type = ats_type
        job.title = job_title
        job.organization = organization
        job.screenshot_path = screenshot_path
        db.commit()

        await emit("status", message=f"Extracted {len(fields_data)} fields. Asking Claude to fill them...")

        # Load profile + Q&A pairs for Claude
        from backend.models.db_models import Profile, QAPair
        profile = db.get(Profile, 1)
        qa_pairs = db.query(QAPair).all()

        filled = await map_fields_to_profile(fields_data, profile, qa_pairs, job_title, organization, ats_type)

        # Save fields to DB
        for i, (raw, mapped) in enumerate(zip(fields_data, filled)):
            field = FormField(
                job_id=job_id,
                page_number=raw.get("page_number", 1),
                field_type=raw.get("field_type", "text"),
                field_label=raw.get("field_label"),
                field_name=raw.get("field_name"),
                field_placeholder=raw.get("field_placeholder"),
                is_required=raw.get("is_required", False),
                options_json=raw.get("options_json"),
                proposed_answer=mapped.get("proposed_answer"),
                confidence=mapped.get("confidence", "missing"),
                reasoning=mapped.get("reasoning"),
                source=mapped.get("source", "missing"),
                final_answer=mapped.get("proposed_answer"),
                display_order=i,
            )
            db.add(field)

        job.status = "ready"
        job.analyzed_at = datetime.utcnow()
        db.commit()

        missing_count = sum(1 for f in filled if f.get("confidence") == "missing")
        if missing_count:
            job.status = "needs_input"
            db.commit()

        await emit("complete", job_id=job_id, missing_count=missing_count)

    except Exception as e:
        db.rollback()
        job = db.get(Job, job_id)
        if job:
            job.status = "pending"
            db.commit()
        await queue.put(sse_event("error", message=str(e)))
    finally:
        db.close()
        _queues.pop(job_id, None)
        _continue_events.pop(job_id, None)
