from datetime import datetime
from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.database import Base


class Profile(Base):
    __tablename__ = "profile"

    id = Column(Integer, primary_key=True, default=1)
    full_name = Column(Text)
    email = Column(Text)
    phone = Column(Text)
    address = Column(Text)
    linkedin = Column(Text)
    website = Column(Text)
    summary = Column(Text)

    # JSON blobs for nested data
    education_json = Column(Text)       # [{degree, field, institution, year, gpa}]
    work_history_json = Column(Text)    # [{title, org, start, end, description}]
    skills_json = Column(Text)          # [string]
    publications_json = Column(Text)    # [{title, journal, year, doi, authors}]
    grants_json = Column(Text)          # [{title, agency, amount, year, role}]
    awards_json = Column(Text)
    fieldwork_json = Column(Text)       # [{location, species, methods, years}]

    # Wildlife biologist-specific
    species_expertise = Column(Text)
    field_sites = Column(Text)
    conservation_philosophy = Column(Text)
    teaching_experience = Column(Text)

    cv_file_path = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class QAPair(Base):
    __tablename__ = "qa_pairs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    tags = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(Text, nullable=False)
    title = Column(Text)
    organization = Column(Text)
    ats_type = Column(Text)  # workday|greenhouse|lever|icims|generic
    status = Column(Text, default="pending")  # pending|analyzing|needs_input|ready|complete
    screenshot_path = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    analyzed_at = Column(DateTime)

    fields = relationship("FormField", back_populates="job", cascade="all, delete-orphan", order_by="FormField.display_order")


class FormField(Base):
    __tablename__ = "form_fields"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, default=1)
    field_type = Column(Text, nullable=False)  # text|textarea|select|radio|checkbox|file|date
    field_label = Column(Text)
    field_name = Column(Text)
    field_placeholder = Column(Text)
    is_required = Column(Boolean, default=False)
    options_json = Column(Text)         # [{value, label}] for select/radio

    proposed_answer = Column(Text)
    confidence = Column(Text)           # high|medium|low|missing
    reasoning = Column(Text)
    source = Column(Text)               # profile|qa_pair|inferred|missing

    final_answer = Column(Text)
    user_edited = Column(Boolean, default=False)
    display_order = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="fields")
