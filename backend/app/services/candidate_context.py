from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.models.job_preference import JobPreference


async def enrich_analysis_with_profile(
    session: AsyncSession, user_id: int, analysis: dict[str, Any]
) -> dict[str, Any]:
    """Merge only explicitly accepted/manual profile data into analysis context."""
    context = dict(analysis)
    candidate = await session.scalar(
        select(Candidate).where(Candidate.user_id == user_id)
    )
    preferences = await session.scalar(
        select(JobPreference).where(JobPreference.user_id == user_id)
    )
    locations: list[str] = []
    if candidate is not None:
        context["profile_full_name"] = candidate.full_name
        context["profile_location"] = candidate.location
        context["profile_years_experience"] = candidate.years_experience
        context["right_to_work_uk"] = candidate.right_to_work_uk
        context["full_uk_driving_licence"] = candidate.full_uk_driving_licence
        context["accepted_profile_enrichment"] = candidate.profile_data.get(
            "accepted_cv_enrichment", {}
        )
    if preferences is not None:
        if preferences.home_location:
            locations.append(preferences.home_location)
        locations.extend(preferences.preferred_locations)
        locations.extend(preferences.preferred_regions)
        context["salary_min"] = preferences.minimum_salary
        context["target_titles"] = (
            preferences.target_titles + preferences.alternative_titles
        )
        context["preferred_industries"] = preferences.industries
        context["excluded_industries"] = preferences.excluded_industries
        context["excluded_companies"] = preferences.excluded_companies
        context["work_arrangements"] = preferences.work_arrangements
        context["employment_types"] = preferences.employment_types
        context["willing_to_travel"] = preferences.willing_to_travel
        context["willing_to_relocate"] = preferences.willing_to_relocate
        context["home_location"] = preferences.home_location
        context["preferred_regions"] = preferences.preferred_regions
        context["search_radius_miles"] = preferences.search_radius_miles
        context["maximum_commute_minutes"] = preferences.maximum_commute_minutes
        context["london_acceptable"] = preferences.london_acceptable
        context["anywhere_uk_acceptable"] = preferences.anywhere_uk_acceptable
        context["remote_acceptable"] = preferences.remote_acceptable
        context["hybrid_acceptable"] = preferences.hybrid_acceptable
        context["relocation_acceptable"] = preferences.relocation_acceptable
    context["preferred_locations"] = list(dict.fromkeys(locations))
    return context
