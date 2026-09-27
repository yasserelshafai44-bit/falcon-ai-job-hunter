from app.job_providers.location import normalize_location
from app.services.match_scoring import JobInput, score_candidate_against_job


def test_uk_location_normalization_distinguishes_london_and_greater_london() -> None:
    london = normalize_location("London, United Kingdom")
    greater = normalize_location("Greater London, UK")
    manchester = normalize_location("Manchester - Main Office")

    assert london.canonical == "gb:london"
    assert greater.canonical == "gb:greater-london"
    assert manchester.canonical == "gb:manchester"


def test_tunbridge_wells_preferences_recognise_explicit_sussex_regions() -> None:
    home = normalize_location("Royal Tunbridge Wells, Kent, UK")
    east_sussex = normalize_location("East Sussex")
    brighton = normalize_location("Brighton & Hove, United Kingdom")

    assert home.region_code == "kent"
    assert east_sussex.region_code == "east-sussex"
    assert brighton.region_code == "east-sussex"

    score = score_candidate_against_job(
        candidate_analysis={
            "role_family": {"value": "Regional Operations Director"},
            "seniority": {"value": "Director"},
            "skills": [{"value": "multi-site operations"}],
            "preferred_locations": [
                "Royal Tunbridge Wells, Kent, UK",
                "East Sussex",
            ],
        },
        job=JobInput(
            title="Operations Manager",
            company="Employer",
            location="Brighton & Hove, United Kingdom",
            description="Lead hospitality operations and teams.",
            remote=False,
        ),
    )
    assert score.location_fit == "good"


def test_remote_location_retains_geographic_eligibility() -> None:
    uk = normalize_location("Remote - United Kingdom", remote=True)
    us = normalize_location("Remote - United States", remote=True)

    assert uk.is_uk is True
    assert us.is_uk is False
    assert uk.canonical != us.canonical


def test_non_uk_remote_role_is_not_geographically_matched() -> None:
    result = score_candidate_against_job(
        candidate_analysis={
            "role_family": {"value": "Regional Operations Director"},
            "seniority": {"value": "Director"},
            "skills": [
                {"value": "multi-site operations"},
                {"value": "P&L management"},
            ],
            "preferred_locations": ["London", "United Kingdom"],
        },
        job=JobInput(
            title="Regional Operations Manager",
            company="Employer",
            location="Remote - United States",
            description="Lead multi-site operations and P&L.",
            remote=True,
            workplace_type="remote",
        ),
    )

    location = next(item for item in result.evidence if item.dimension == "location")
    assert location.status == "mismatched"
    assert result.overall_score <= 79
