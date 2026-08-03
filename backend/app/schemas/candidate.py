from typing import Any

from pydantic import BaseModel, EmailStr, Field


class CandidateUpsert(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    phone: str | None = None
    location: str | None = None
    years_experience: int = Field(default=0, ge=0, le=70)
    right_to_work_uk: bool = False
    full_uk_driving_licence: bool = False
    profile_data: dict[str, Any] = Field(default_factory=dict)


class CandidateResponse(CandidateUpsert):
    id: int
    user_id: int

    model_config = {"from_attributes": True}
