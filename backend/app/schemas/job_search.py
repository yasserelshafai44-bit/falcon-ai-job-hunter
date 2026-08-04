from datetime import datetime

from pydantic import BaseModel, Field


class JobRead(BaseModel):
    id: int
    provider: str
    external_id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    remote: bool
    salary_min: int | None
    salary_max: int | None
    currency: str | None
    posted_at: datetime | None
    discovered_at: datetime

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
    limit_per_provider: int = Field(default=50, ge=1, le=200)


class JobSyncResponse(BaseModel):
    providers_requested: list[str]
    discovered: int
    inserted: int
    updated: int
    provider_errors: dict[str, str] = Field(default_factory=dict)
