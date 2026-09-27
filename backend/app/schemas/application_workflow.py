from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


class ApplicationWorkflowStatus(StrEnum):
    DRAFT = "draft"
    MATERIALS_READY = "materials_ready"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    WITHDRAWN = "withdrawn"
    REJECTED = "rejected"
    INTERVIEW = "interview"
    OFFER = "offer"


class CreateApplicationWorkflowRequest(BaseModel):
    job_match_id: int


class AttachApplicationDocumentsRequest(BaseModel):
    resume_document_id: int
    cover_letter_document_id: int | None = None


class ApprovalRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)


class SubmissionRequest(BaseModel):
    external_application_url: HttpUrl | None = None
    confirmed_submitted: bool = False


class OutcomeRequest(BaseModel):
    status: ApplicationWorkflowStatus


class ApplicationWorkflowRead(BaseModel):
    id: int
    user_id: int
    job_match_id: int
    job_id: int
    resume_document_id: int | None
    cover_letter_document_id: int | None
    status: ApplicationWorkflowStatus
    application_method: str = "ASSISTED_APPLY"
    continued_at: datetime | None = None
    approval_notes: str | None
    external_application_url: str | None
    submitted_at: datetime | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationWorkflowList(BaseModel):
    items: list[ApplicationWorkflowRead]
    total: int


class ReviewJob(BaseModel):
    id: int
    title: str
    company: str
    location: str
    description: str
    url: str


class ReviewMatch(BaseModel):
    id: int
    overall_score: int
    recommendation: str
    strengths: list[str]
    gaps: list[str]
    mandatory_failures: list[str]
    evidence: list[dict[str, Any]]
    uncertainty: list[str]


class ReviewDocument(BaseModel):
    id: int
    document_type: str
    content: str
    status: str
    metadata: dict[str, Any]
    updated_at: datetime
    change_summary: list[str] = Field(default_factory=list)


class ApplicationReview(BaseModel):
    application_route: dict[str, Any] = Field(default_factory=dict)
    workflow: ApplicationWorkflowRead
    job: ReviewJob
    match: ReviewMatch
    original_cv_evidence: dict[str, Any]
    original_cv_text: str = ""
    resume: ReviewDocument
    cover_letter: ReviewDocument
    unanswered_employer_questions: list[str] = Field(default_factory=list)
    employer_questions_status: Literal[
        "retrieved", "none_required", "requires_employer_site", "unavailable", "unknown"
    ] = "unknown"
    employer_questions_note: str = "Employer questions: not yet checked."
    automated_submission_supported: bool = False
    status_history: list["ApplicationStatusEventRead"] = Field(default_factory=list)


class ApplicationStatusEventRead(BaseModel):
    from_status: str | None
    to_status: str
    event_type: str
    created_at: datetime

    model_config = {"from_attributes": True}
