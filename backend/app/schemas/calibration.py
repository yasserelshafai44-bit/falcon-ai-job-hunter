from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class HumanMatchLabel(StrEnum):
    STRONG_MATCH = "strong_match"
    GOOD_MATCH = "good_match"
    ADJACENT = "adjacent"
    WEAK_MATCH = "weak_match"
    REJECT = "reject"


class CorpusBuildRequest(BaseModel):
    candidate_analysis_id: int
    providers: list[str] = Field(default_factory=lambda: ["deliveroo", "kfc_uk"])
    corpus_version: str = Field(default="live-v1", min_length=1, max_length=32)


class ValidationSampleRequest(BaseModel):
    candidate_analysis_id: int
    providers: list[str] = Field(default_factory=list)
    corpus_version: str = Field(
        default="beta-validation-v1", min_length=1, max_length=32
    )
    sample_size: int = Field(default=12, ge=10, le=15)


class ReviewUpdate(BaseModel):
    human_label: HumanMatchLabel
    reviewer_notes: str | None = Field(default=None, max_length=4000)


class CalibrationReviewRead(BaseModel):
    id: int
    candidate_analysis_id: int
    job_id: int
    human_label: HumanMatchLabel | None
    reviewer_notes: str | None
    vacancy_snapshot: dict
    falcon_snapshot: dict
    human_review_summary: dict
    corpus_version: str
    reviewed: bool
    reviewer_id: int
    reviewer_email: str
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CalibrationReviewList(BaseModel):
    items: list[CalibrationReviewRead]
    total: int
    reviewed: int


class CalibrationEvaluation(BaseModel):
    corpus_version: str
    reviewed: int
    unreviewed: int
    human_label_distribution: dict[str, int]
    strong_apply_precision: float | None
    apply_precision: float | None
    false_positive_rate: float | None
    false_negative_rate: float | None
    confusion_matrix: dict[str, dict[str, int]]
    ranking_order_accuracy: float | None
    score_distribution_by_human_label: dict[str, dict]
