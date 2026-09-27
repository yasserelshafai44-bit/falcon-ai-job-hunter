from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CalibrationReview(Base):
    """Independent human assessment of a real vacancy and Falcon score snapshot."""

    __tablename__ = "calibration_reviews"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "candidate_analysis_id",
            "job_id",
            "corpus_version",
            name="uq_calibration_review",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    candidate_analysis_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_analyses.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("discovered_jobs.id", ondelete="RESTRICT"), index=True
    )
    human_label: Mapped[str | None] = mapped_column(
        String(32), nullable=True, index=True
    )
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    vacancy_snapshot: Mapped[dict] = mapped_column(JSON)
    falcon_snapshot: Mapped[dict] = mapped_column(JSON)
    corpus_version: Mapped[str] = mapped_column(String(32), default="live-v1")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
