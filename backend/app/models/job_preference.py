from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class JobPreference(Base):
    """A user's job-search preferences."""

    __tablename__ = "job_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    target_titles: Mapped[list[str]] = mapped_column(JSON, default=list)
    alternative_titles: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_locations: Mapped[list[str]] = mapped_column(JSON, default=list)
    home_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_regions: Mapped[list[str]] = mapped_column(JSON, default=list)
    search_radius_miles: Mapped[int | None] = mapped_column(Integer, nullable=True)
    maximum_commute_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    london_acceptable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    anywhere_uk_acceptable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    remote_acceptable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    hybrid_acceptable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    relocation_acceptable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    work_arrangements: Mapped[list[str]] = mapped_column(JSON, default=list)
    industries: Mapped[list[str]] = mapped_column(JSON, default=list)
    excluded_industries: Mapped[list[str]] = mapped_column(JSON, default=list)
    excluded_companies: Mapped[list[str]] = mapped_column(JSON, default=list)
    employment_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    willing_to_travel: Mapped[bool] = mapped_column(Boolean, default=False)
    willing_to_relocate: Mapped[bool] = mapped_column(Boolean, default=False)
    minimum_salary: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="GBP")
    requires_sponsorship: Mapped[bool] = mapped_column(Boolean, default=False)
