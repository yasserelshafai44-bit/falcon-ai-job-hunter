from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ApplicationWorkflow(Base):
    """Human-approved workflow for a job application."""

    __tablename__ = "application_workflows"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "job_match_id",
            name="uq_application_workflow_user_match",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    job_match_id: Mapped[int] = mapped_column(
        ForeignKey("job_matches.id", ondelete="CASCADE"),
        index=True,
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("discovered_jobs.id", ondelete="CASCADE"),
        index=True,
    )
    resume_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("generated_documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    cover_letter_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("generated_documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    approval_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_application_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
