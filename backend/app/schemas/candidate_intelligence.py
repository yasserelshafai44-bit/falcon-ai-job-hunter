from datetime import datetime

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    value: str
    source_text: str
    confidence: float = Field(ge=0, le=1)


class CandidateIntelligenceData(BaseModel):
    professional_summary: str = ""
    professional_summary_evidence: EvidenceItem | None = None
    full_name: EvidenceItem | None = None
    primary_location: EvidenceItem | None = None
    years_experience: EvidenceItem | None = None
    seniority: EvidenceItem | None = None
    role_family: EvidenceItem | None = None
    skills: list[EvidenceItem] = Field(default_factory=list)
    achievements: list[EvidenceItem] = Field(default_factory=list)
    industries: list[EvidenceItem] = Field(default_factory=list)
    leadership_scope: list[EvidenceItem] = Field(default_factory=list)
    career_tracks: list[str] = Field(default_factory=list)
    career_track_evidence: list[EvidenceItem] = Field(default_factory=list)
    certifications_qualifications: list[EvidenceItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CandidateAnalysisResponse(BaseModel):
    id: int
    cv_document_id: int
    analysis: CandidateIntelligenceData
    created_at: datetime
    updated_at: datetime


class ApplyProfileSuggestionsRequest(BaseModel):
    fields: list[str] = Field(default_factory=list, max_length=20)
