from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ProviderRefreshRun(Base):
    """Auditable provider refresh statistics and drift alerts."""

    __tablename__ = "provider_refresh_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(24))
    jobs_retrieved: Mapped[int] = mapped_column(Integer, default=0)
    new_jobs: Mapped[int] = mapped_column(Integer, default=0)
    changed_jobs: Mapped[int] = mapped_column(Integer, default=0)
    closed_jobs: Mapped[int] = mapped_column(Integer, default=0)
    failures: Mapped[dict] = mapped_column(JSON, default=dict)
    score_distribution: Mapped[dict] = mapped_column(JSON, default=dict)
    recommendation_distribution: Mapped[dict] = mapped_column(JSON, default=dict)
    occupational_family_distribution: Mapped[dict] = mapped_column(JSON, default=dict)
    alerts: Mapped[list[dict]] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
