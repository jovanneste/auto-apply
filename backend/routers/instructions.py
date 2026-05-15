from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.db_models import Job

router = APIRouter(prefix="/api/instructions", tags=["instructions"])


@router.post("/{job_id}/generate")
async def generate_instructions(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.fields:
        raise HTTPException(status_code=400, detail="No fields found for this job. Run analysis first.")

    from backend.services.claude_service import generate_instructions_stream

    async def streamer():
        async for chunk in generate_instructions_stream(job):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        streamer(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
