from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CandidateAnalysis(Base):
    """Structured candidate intelligence extracted from one CV."""

    __tablename__ = "candidate_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cv_document_id: Mapped[int] = mapped_column(
        ForeignKey("cv_documents.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    extracted_text: Mapped[str] = mapped_column(Text)
    analysis_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
