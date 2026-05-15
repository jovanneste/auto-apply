import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.db_models import Profile, QAPair
from backend.models.schemas import ProfileResponse, ProfileUpdate, QAPairCreate, QAPairResponse
from backend.config import CV_DIR

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _get_or_create_profile(db: Session) -> Profile:
    profile = db.get(Profile, 1)
    if not profile:
        profile = Profile(id=1)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("", response_model=ProfileResponse)
def get_profile(db: Session = Depends(get_db)):
    return _get_or_create_profile(db)


@router.put("", response_model=ProfileResponse)
def update_profile(data: ProfileUpdate, db: Session = Depends(get_db)):
    profile = _get_or_create_profile(db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/upload-cv", response_model=ProfileResponse)
async def upload_cv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    dest = CV_DIR / "cv.pdf"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    profile = _get_or_create_profile(db)
    profile.cv_file_path = str(dest)
    db.commit()

    # Kick off parsing in background (Phase 2 wires this up fully)
    from backend.services.pdf_parser import parse_and_store_cv
    await parse_and_store_cv(str(dest), db)

    db.refresh(profile)
    return profile


# ── Q&A Pairs ──────────────────────────────────────────────────────────────

@router.get("/qa-pairs", response_model=list[QAPairResponse])
def list_qa_pairs(db: Session = Depends(get_db)):
    return db.query(QAPair).order_by(QAPair.id).all()


@router.post("/qa-pairs", response_model=QAPairResponse, status_code=201)
def create_qa_pair(data: QAPairCreate, db: Session = Depends(get_db)):
    pair = QAPair(**data.model_dump())
    db.add(pair)
    db.commit()
    db.refresh(pair)
    return pair


@router.put("/qa-pairs/{pair_id}", response_model=QAPairResponse)
def update_qa_pair(pair_id: int, data: QAPairCreate, db: Session = Depends(get_db)):
    pair = db.get(QAPair, pair_id)
    if not pair:
        raise HTTPException(status_code=404, detail="Q&A pair not found")
    for field, value in data.model_dump().items():
        setattr(pair, field, value)
    db.commit()
    db.refresh(pair)
    return pair


@router.delete("/qa-pairs/{pair_id}", status_code=204)
def delete_qa_pair(pair_id: int, db: Session = Depends(get_db)):
    pair = db.get(QAPair, pair_id)
    if not pair:
        raise HTTPException(status_code=404, detail="Q&A pair not found")
    db.delete(pair)
    db.commit()
