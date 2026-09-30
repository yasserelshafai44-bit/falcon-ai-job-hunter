from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class JobRead(BaseModel):
    id: int
    provider: str
    external_id: str
    canonical_key: str | None
    canonical_url: str | None
    title: str
    company: str
    location: str
    description: str
    url: str
    remote: bool
    is_demo: bool
    is_active: bool
    workplace_type: str
    requirements: list[str]
    source_records: list[dict]
    employment_type: str | None
    salary_min: int | None
    salary_max: int | None
    currency: str | None
    posted_at: datetime | None
    expires_at: datetime | None
    discovered_at: datetime
    last_seen_at: datetime
    closed_at: datetime | None

    model_config = {"from_attributes": True}


class JobSearchResponse(BaseModel):
    items: list[JobRead]
    total: int
    page: int
    page_size: int


class JobSyncRequest(BaseModel):
    keyword: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=120)
    providers: list[str] = Field(default_factory=lambda: ["remoteok"])
    limit_per_provider: int = Field(default=10000, ge=1, le=10000)
    candidate_analysis_id: int | None = None
    refresh: bool = True


class JobSyncResponse(BaseModel):
    providers_requested: list[str]
    discovered: int
    inserted: int
    updated: int
    duplicates: int
    closed: int
    provider_errors: dict[str, str] = Field(default_factory=dict)
    refresh_run_ids: list[int] = Field(default_factory=list)


class JobProviderRead(BaseModel):
    id: str
    name: str
    kind: str
    credentials_required: bool
    source_url: str | None = None
    recommended_refresh_minutes: int | None = None


class EmployerRegistryRead(BaseModel):
    id: str
    employer: str
    category: str
    status: str
    provider: str | None
    careers_url: str
    reason: str
    live_vacancies: int | None = None
    latest_refresh_vacancies: int | None = None
    last_checked_at: datetime | None = None
    last_successful_refresh: datetime | None = None
    latest_refresh_status: str | None = None
    latest_refresh_error: str | None = None


class ManualJobImport(BaseModel):
    candidate_analysis_id: int
    source_url: str | None = Field(default=None, max_length=2000)
    employer: str = Field(min_length=2, max_length=255)
    title: str = Field(min_length=2, max_length=255)
    location: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=80, max_length=100_000)
    workplace_type: str = Field(
        default="unknown", pattern="^(unknown|on-site|hybrid|remote)$"
    )
    requirements: list[str] = Field(default_factory=list, max_length=50)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default="GBP", min_length=3, max_length=3)

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        value = value.strip()
        if not value.startswith("https://"):
            raise ValueError("Official vacancy URL must use HTTPS")
        return value


class ManualJobImportResponse(BaseModel):
    job: JobRead
    match: "JobMatchRead"
    created: bool
    message: str


from app.schemas.job_matching import JobMatchRead  # noqa: E402

ManualJobImportResponse.model_rebuild()
