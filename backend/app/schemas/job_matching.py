from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class MatchRecommendation(StrEnum):
    STRONG_APPLY = "strong_apply"
    APPLY = "apply"
    REVIEW = "review"
    WEAK_MATCH = "weak_match"
    REJECT = "reject"


class MatchEvidence(BaseModel):
    dimension: str
    contribution: float
    explanation: str
    sources: list[str] = Field(default_factory=list)


class MatchScore(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    recommendation: MatchRecommendation
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    mandatory_failures: list[str] = Field(default_factory=list)
    evidence: list[MatchEvidence] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    recommended_cv_track: str | None = None
    recommended_next_action: str


class ScoreJobRequest(BaseModel):
    candidate_analysis_id: int


class RecalculateMatchesRequest(BaseModel):
    candidate_analysis_id: int
    job_ids: list[int] = Field(default_factory=list, max_length=250)


class JobMatchRead(MatchScore):
    id: int
    user_id: int
    candidate_analysis_id: int
    job_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobMatchList(BaseModel):
    items: list[JobMatchRead]
    total: int


class RecalculateMatchesResponse(BaseModel):
    updated: int
    failed_job_ids: list[int] = Field(default_factory=list)
