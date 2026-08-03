from pydantic import BaseModel, Field


class JobPreferenceUpsert(BaseModel):
    target_titles: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    work_arrangements: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    minimum_salary: int | None = Field(default=None, ge=0)
    currency: str = Field(default="GBP", min_length=3, max_length=3)
    requires_sponsorship: bool = False


class JobPreferenceResponse(JobPreferenceUpsert):
    id: int
    user_id: int

    model_config = {"from_attributes": True}
