from datetime import datetime
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field

class GeneratedDocumentType(StrEnum):
    RESUME = "resume"
    COVER_LETTER = "cover_letter"

class GeneratedDocumentStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    ARCHIVED = "archived"

class GenerateDocumentRequest(BaseModel):
    candidate_analysis_id: int
    job_id: int
    tone: str = Field(default="professional", max_length=60)
    max_words: int = Field(default=650, ge=150, le=1200)

class GeneratedDocumentRead(BaseModel):
    id: int
    user_id: int
    candidate_analysis_id: int
    job_id: int
    document_type: GeneratedDocumentType
    provider: str
    prompt_version: str
    content: str
    metadata_json: dict[str, Any]
    status: GeneratedDocumentStatus
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class GenerationHistoryResponse(BaseModel):
    items: list[GeneratedDocumentRead]
    total: int
