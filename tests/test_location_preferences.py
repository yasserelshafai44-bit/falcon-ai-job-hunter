import subprocess
from pathlib import Path

import pytest
from app.services.match_scoring import JobInput, score_candidate_against_job

from tests.test_manual_vacancy_and_registry import analysed_candidate, manual_payload
from tests.test_production_ranking import candidate

PREFERENCES = {
    "home_location": "Royal Tunbridge Wells, Kent, UK",
    "preferred_locations": ["London"],
    "preferred_regions": ["Kent"],
    "london_acceptable": True,
    "remote_acceptable": True,
    "hybrid_acceptable": True,
    "anywhere_uk_acceptable": None,
}


@pytest.mark.parametrize(
    "location,mode,expected",
    [
        ("London, UK", "on-site", "good"),
        ("Maidstone, Kent, UK", "on-site", "good"),
        ("Royal Tunbridge Wells, Kent, UK", "on-site", "good"),
        ("Bristol, UK", "on-site", "unknown"),
        ("Brighton, UK", "on-site", "unknown"),
        ("UK", "on-site", "unknown"),
        ("Remote UK", "remote", "good"),
        ("Manchester, UK", "hybrid", "good"),
        ("Remote", "remote", "unknown"),
        ("Location not specified", "unknown", "unknown"),
        ("New York, United States", "remote", "outside_preference"),
    ],
)
def test_explicit_geography_never_changes_career_fit(location, mode, expected):
    job = JobInput(
        title="Regional Operations Manager",
        company="Example",
        description="Lead multi-site restaurant operations, P&L and teams.",
        location=location,
        workplace_type=mode,
        remote=mode == "remote",
    )
    baseline = score_candidate_against_job(candidate_analysis=candidate(), job=job)
    result = score_candidate_against_job(
        candidate_analysis={**candidate(), **PREFERENCES}, job=job
    )
    assert result.location_fit == expected
    assert result.location_fit_explanation
    assert result.career_fit_score == baseline.career_fit_score
    assert result.recommendation == baseline.recommendation


def test_home_country_and_relocation_are_not_blanket_approval():
    from app.services.location_fit import assess_location

    context = {
        "home_location": PREFERENCES["home_location"],
        "relocation_acceptable": True,
        "willing_to_travel": True,
    }
    for place in ["Maidstone, Kent, UK", "Manchester, UK", "UK"]:
        assert assess_location(context, place)[1] == "unknown"
    assert (
        assess_location(
            {**PREFERENCES, "anywhere_uk_acceptable": False}, "Manchester, UK"
        )[1]
        == "mismatched"
    )
    assert (
        assess_location(
            {**PREFERENCES, "anywhere_uk_acceptable": True}, "Manchester, UK"
        )[1]
        == "matched"
    )
    for mode in ["remote", "hybrid"]:
        assert (
            assess_location(
                {**PREFERENCES, f"{mode}_acceptable": False},
                "London, UK",
                workplace_type=mode,
            )[1]
            == "mismatched"
        )


@pytest.mark.asyncio
async def test_saved_preferences_refresh_only_own_location_and_preserve_career(client):
    headers, analysis_id = await analysed_candidate(client)
    payload = manual_payload(
        analysis_id,
        title="Regional Operations Manager",
        description=(
            "Lead multi-site restaurant teams and P&L. Coach area managers, "
            "own regional performance and develop restaurant managers."
        ),
    )
    payload.update(location="Bristol, UK", workplace_type="on-site")
    response = await client.post("/api/v1/jobs/manual", headers=headers, json=payload)
    assert response.status_code == 200
    before = response.json()["match"]
    await client.put(
        "/api/v1/preferences",
        headers=headers,
        json={**PREFERENCES, "minimum_salary": 60000},
    )
    saved = (await client.get("/api/v1/preferences", headers=headers)).json()
    assert all(saved[key] == value for key, value in PREFERENCES.items())
    await client.put(
        "/api/v1/preferences", headers=headers, json={"anywhere_uk_acceptable": True}
    )
    matches = (await client.get("/api/v1/matches", headers=headers)).json()["items"]
    assert matches[0]["location_fit"] == "good"
    after = matches[0]
    for key in ["id", "career_fit_score", "recommendation", "strengths", "gaps"]:
        assert after[key] == before[key]
    saved = (await client.get("/api/v1/preferences", headers=headers)).json()
    assert saved["minimum_salary"] == 60000
    assert saved["home_location"] == PREFERENCES["home_location"]
    other = await client.post(
        "/api/v1/auth/register",
        json={"email": "other-location@example.com", "password": "SecurePass123!"},
    )
    other_headers = {"Authorization": "Bearer " + other.json()["access_token"]}
    await client.put(
        "/api/v1/preferences",
        headers=other_headers,
        json={"anywhere_uk_acceptable": False},
    )
    assert (await client.get("/api/v1/matches", headers=headers)).json()["items"][
        0
    ] == after


def test_real_preference_form_save_reload():
    result = subprocess.run(
        ["node", str(Path(__file__).with_name("frontend_location_preferences.mjs"))],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr
