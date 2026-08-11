from datetime import datetime
from enum import StrEnum

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
    approval_notes: str | None
    external_application_url: str | None
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationWorkflowList(BaseModel):
    items: list[ApplicationWorkflowRead]
    total: int
