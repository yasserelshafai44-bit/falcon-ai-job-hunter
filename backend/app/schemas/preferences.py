from pydantic import BaseModel, Field

DEFAULT_HOME_LOCATION = "Royal Tunbridge Wells, Kent, UK"
DEFAULT_PREFERRED_LOCATIONS = ["Royal Tunbridge Wells", "Tunbridge Wells"]
DEFAULT_PREFERRED_REGIONS = [
    "Kent",
    "East Sussex",
    "West Sussex",
    "South East England",
]


class JobPreferenceUpsert(BaseModel):
    target_titles: list[str] = Field(default_factory=list)
    alternative_titles: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(
        default_factory=lambda: list(DEFAULT_PREFERRED_LOCATIONS)
    )
    home_location: str | None = Field(default=DEFAULT_HOME_LOCATION, max_length=255)
    preferred_regions: list[str] = Field(
        default_factory=lambda: list(DEFAULT_PREFERRED_REGIONS)
    )
    search_radius_miles: int | None = Field(default=None, ge=0, le=1000)
    maximum_commute_minutes: int | None = Field(default=None, ge=0, le=600)
    london_acceptable: bool | None = True
    anywhere_uk_acceptable: bool | None = None
    remote_acceptable: bool | None = True
    hybrid_acceptable: bool | None = True
    relocation_acceptable: bool | None = None
    work_arrangements: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    excluded_industries: list[str] = Field(default_factory=list)
    excluded_companies: list[str] = Field(default_factory=list)
    employment_types: list[str] = Field(default_factory=list)
    willing_to_travel: bool = False
    willing_to_relocate: bool = False
    minimum_salary: int | None = Field(default=None, ge=0)
    currency: str = Field(default="GBP", min_length=3, max_length=3)
    requires_sponsorship: bool = False


class JobPreferenceResponse(JobPreferenceUpsert):
    id: int
    user_id: int

    model_config = {"from_attributes": True}
