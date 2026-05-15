from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel


# ── Profile ──────────────────────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None
    summary: Optional[str] = None
    education_json: Optional[str] = None
    work_history_json: Optional[str] = None
    skills_json: Optional[str] = None
    publications_json: Optional[str] = None
    grants_json: Optional[str] = None
    awards_json: Optional[str] = None
    fieldwork_json: Optional[str] = None
    species_expertise: Optional[str] = None
    field_sites: Optional[str] = None
    conservation_philosophy: Optional[str] = None
    teaching_experience: Optional[str] = None


class ProfileResponse(ProfileUpdate):
    id: int
    cv_file_path: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Q&A Pairs ─────────────────────────────────────────────────────────────────

class QAPairCreate(BaseModel):
    question: str
    answer: str
    tags: Optional[str] = None


class QAPairResponse(QAPairCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Jobs ─────────────────────────────────────────────────────────────────────

class JobCreate(BaseModel):
    url: str


class JobUpdate(BaseModel):
    title: Optional[str] = None
    organization: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class FormFieldResponse(BaseModel):
    id: int
    job_id: int
    page_number: int
    field_type: str
    field_label: Optional[str] = None
    field_name: Optional[str] = None
    field_placeholder: Optional[str] = None
    is_required: bool
    options_json: Optional[str] = None
    proposed_answer: Optional[str] = None
    confidence: Optional[str] = None
    reasoning: Optional[str] = None
    source: Optional[str] = None
    final_answer: Optional[str] = None
    user_edited: bool
    display_order: Optional[int] = None

    model_config = {"from_attributes": True}


class JobSummaryResponse(BaseModel):
    id: int
    url: str
    title: Optional[str] = None
    organization: Optional[str] = None
    ats_type: Optional[str] = None
    status: str
    created_at: datetime
    analyzed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class JobDetailResponse(JobSummaryResponse):
    screenshot_path: Optional[str] = None
    notes: Optional[str] = None
    fields: List[FormFieldResponse] = []

    model_config = {"from_attributes": True}


# ── Field update ──────────────────────────────────────────────────────────────

class FieldUpdate(BaseModel):
    final_answer: str
