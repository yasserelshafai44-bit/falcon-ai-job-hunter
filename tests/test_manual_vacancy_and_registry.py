import pytest
from app.job_providers.employer_registry import (
    EMPLOYER_REGISTRY,
    live_direct_provider_keys,
    resolve_provider_selection,
)
from app.job_providers.factory import build_job_providers
from httpx import AsyncClient


async def analysed_candidate(client: AsyncClient) -> tuple[dict[str, str], int]:
    auth = await client.post(
        "/api/v1/auth/register",
        json={"email": "manual-review@example.com", "password": "VerySecure123!"},
    )
    headers = {"Authorization": f"Bearer {auth.json()['access_token']}"}
    uploaded = await client.post(
        "/api/v1/cvs",
        headers=headers,
        files={
            "file": (
                "candidate.txt",
                """Senior Regional Operations Director with 20 years in QSR and
                hospitality. Led 100 restaurants across multiple regions with full
                P&L, KPI, inventory, franchise and people leadership accountability.""",
                "text/plain",
            )
        },
    )
    analysed = await client.post(
        f"/api/v1/candidate-intelligence/cvs/{uploaded.json()['id']}/analyze",
        headers=headers,
    )
    return headers, analysed.json()["id"]


@pytest.mark.asyncio
async def test_registry_distinguishes_live_from_unsearchable(
    client: AsyncClient,
) -> None:
    headers, _ = await analysed_candidate(client)
    response = await client.get("/api/v1/jobs/employers", headers=headers)
    assert response.status_code == 200
    entries = {entry["employer"]: entry for entry in response.json()}
    assert entries["Deliveroo"]["status"] == "LIVE"
    assert entries["Raising Cane's UK"]["status"] == "LIVE"
    assert entries["Greene King"]["status"] == "LIVE"
    assert entries["Burger King UK"]["status"] == "AUTHORIZATION_REQUIRED"
    assert entries["Wingstop UK"]["status"] == "AUTHORIZATION_REQUIRED"
    assert entries["Starbucks UK"]["status"] == "MANUAL_ONLY"
    assert entries["Burger King UK"]["provider"] is None
    assert entries["Burger King UK"]["live_vacancies"] is None
    assert entries["Burger King UK"]["latest_refresh_vacancies"] is None
    assert entries["Burger King UK"]["last_checked_at"] is not None
    assert entries["Deliveroo"]["live_vacancies"] == 0


def test_all_verified_direct_resolves_every_live_provider_only() -> None:
    expected = tuple(
        entry["provider"]
        for entry in EMPLOYER_REGISTRY
        if entry["status"] == "LIVE" and entry["provider"]
    )
    resolved = resolve_provider_selection(["all_verified_direct"])
    assert tuple(resolved) == expected == live_direct_provider_keys()
    assert {provider.name for provider in build_job_providers(set(resolved))} == set(
        expected
    )
    inaccessible = {
        entry["provider"]
        for entry in EMPLOYER_REGISTRY
        if entry["status"] != "LIVE" and entry["provider"]
    }
    assert not set(resolved) & inaccessible


@pytest.mark.asyncio
async def test_default_location_profile_is_explicit_without_invented_commute(
    client: AsyncClient,
) -> None:
    headers, _ = await analysed_candidate(client)
    response = await client.put("/api/v1/preferences", headers=headers, json={})
    assert response.status_code == 200
    data = response.json()
    assert data["home_location"] == "Royal Tunbridge Wells, Kent, UK"
    assert data["preferred_locations"] == [
        "Royal Tunbridge Wells",
        "Tunbridge Wells",
    ]
    assert data["preferred_regions"] == [
        "Kent",
        "East Sussex",
        "West Sussex",
        "South East England",
    ]
    assert data["search_radius_miles"] is None
    assert data["maximum_commute_minutes"] is None
    assert data["london_acceptable"] is True
    assert data["hybrid_acceptable"] is True
    assert data["remote_acceptable"] is True
    assert data["relocation_acceptable"] is None


def manual_payload(analysis_id: int, *, title: str, description: str) -> dict:
    return {
        "candidate_analysis_id": analysis_id,
        "source_url": "https://careers.example-employer.co.uk/jobs/operations-123",
        "employer": "Example QSR UK",
        "title": title,
        "location": "Royal Tunbridge Wells, Kent, UK",
        "workplace_type": "hybrid",
        "description": description,
        "requirements": ["Multi-site restaurant leadership experience"],
    }


@pytest.mark.asyncio
async def test_manual_official_import_ranks_and_deduplicates_url(
    client: AsyncClient,
) -> None:
    headers, analysis_id = await analysed_candidate(client)
    preferences = await client.put("/api/v1/preferences", headers=headers, json={})
    assert preferences.status_code == 200
    payload = manual_payload(
        analysis_id,
        title="Regional Operations Manager",
        description=(
            "Lead a regional portfolio of 30 QSR restaurants with full P&L, KPI, "
            "inventory, franchise partner and people leadership accountability. "
            "Coach area managers and deliver continuous operational improvement."
        ),
    )
    created = await client.post("/api/v1/jobs/manual", headers=headers, json=payload)
    assert created.status_code == 200
    first = created.json()
    assert first["created"] is True
    assert first["job"]["provider"] == "manual_official"
    assert first["match"]["career_fit_score"] >= 78
    assert first["match"]["recommendation"] in {"apply", "strong_apply"}
    assert first["match"]["location_fit"] == "good"

    payload["description"] += " Travel within Kent is explicitly required."
    repeated = await client.post("/api/v1/jobs/manual", headers=headers, json=payload)
    assert repeated.status_code == 200
    second = repeated.json()
    assert second["created"] is False
    assert second["job"]["id"] == first["job"]["id"]
    jobs = await client.get(
        "/api/v1/jobs",
        headers=headers,
        params={"provider": "manual_official", "page_size": 100},
    )
    assert jobs.json()["total"] == 1


@pytest.mark.asyncio
async def test_manual_irrelevant_vacancy_is_stored_but_rejected(
    client: AsyncClient,
) -> None:
    headers, analysis_id = await analysed_candidate(client)
    payload = manual_payload(
        analysis_id,
        title="Senior Software Engineering Manager",
        description=(
            "Lead software delivery operations, regional engineering leadership, "
            "commercial KPIs and platform architecture. Expert Python and cloud "
            "engineering experience is mandatory for this specialist technology role."
        ),
    )
    payload["source_url"] = "https://careers.example-employer.co.uk/jobs/software-9"
    response = await client.post("/api/v1/jobs/manual", headers=headers, json=payload)
    assert response.status_code == 200
    assert response.json()["job"]["provider"] == "manual_official"
    assert response.json()["match"]["recommendation"] == "reject"
    assert response.json()["match"]["career_fit_score"] <= 24


@pytest.mark.asyncio
async def test_manual_import_requires_authentication_and_valid_input(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/jobs/manual",
        json=manual_payload(
            1,
            title="Regional Operations Manager",
            description="Valid long description " * 10,
        ),
    )
    assert response.status_code == 401
    headers, analysis_id = await analysed_candidate(client)
    invalid = manual_payload(
        analysis_id,
        title="Regional Operations Manager",
        description="Too short",
    )
    invalid["source_url"] = "http://insecure.example/jobs/1"
    response = await client.post("/api/v1/jobs/manual", headers=headers, json=invalid)
    assert response.status_code == 422
