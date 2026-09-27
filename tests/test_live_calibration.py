from datetime import UTC, datetime

import pytest
from app.database.session import get_db_session
from app.main import app
from app.models.calibration_review import CalibrationReview
from app.models.discovered_job import DiscoveredJob
from app.models.job_match import JobMatch
from httpx import AsyncClient
from sqlalchemy import select


@pytest.mark.asyncio
async def test_real_corpus_requires_independent_human_label(
    client: AsyncClient,
) -> None:
    auth = await client.post(
        "/api/v1/auth/register",
        json={"email": "reviewer@example.com", "password": "VerySecure123!"},
    )
    headers = {"Authorization": f"Bearer {auth.json()['access_token']}"}
    uploaded = await client.post(
        "/api/v1/cvs",
        headers=headers,
        files={
            "file": (
                "operations.txt",
                "ALEX REVIEW\nRegional Operations Director\nLondon, UK\n"
                "22+ years of experience in multi-site QSR operations, P&L, "
                "team leadership, KPI management and franchise compliance.",
                "text/plain",
            )
        },
    )
    analysis = await client.post(
        f"/api/v1/candidate-intelligence/cvs/{uploaded.json()['id']}/analyze",
        headers=headers,
    )
    session_factory = app.dependency_overrides[get_db_session]
    async for session in session_factory():
        job = DiscoveredJob(
            provider="deliveroo",
            external_id="real-review-1",
            canonical_key="real-review-key",
            canonical_url="https://careers.deliveroo.co.uk/role/real-review-1/",
            title="Regional Operations Manager",
            company="Deliveroo",
            location="London, UK",
            description=(
                "Lead multi-site restaurant operations, P&L and regional teams."
            ),
            url="https://careers.deliveroo.co.uk/role/real-review-1/",
            remote=False,
            is_demo=False,
            is_active=True,
            workplace_type="hybrid",
            requirements=[],
            source_records=[],
            last_seen_at=datetime.now(UTC),
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        job_id = job.id
        break
    scored = await client.post(
        f"/api/v1/matches/jobs/{job_id}/score",
        headers=headers,
        json={"candidate_analysis_id": analysis.json()["id"]},
    )
    assert scored.status_code == 200
    corpus = await client.post(
        "/api/v1/calibration/corpus",
        headers=headers,
        json={
            "candidate_analysis_id": analysis.json()["id"],
            "providers": ["deliveroo"],
            "corpus_version": "live-v1",
        },
    )
    assert corpus.status_code == 200
    review = corpus.json()["items"][0]
    assert review["human_label"] is None
    assert review["reviewed"] is False
    assert review["reviewer_email"] == "reviewer@example.com"
    assert review["vacancy_snapshot"]["vacancy_id"] == "real-review-1"
    assert review["falcon_snapshot"]["score"] == scored.json()["overall_score"]
    assert review["human_review_summary"]["title"] == "Regional Operations Manager"
    assert review["human_review_summary"]["employer"] == "Deliveroo"
    assert review["human_review_summary"]["salary"] == "NOT STATED"

    before = await client.get("/api/v1/calibration/evaluation", headers=headers)
    assert before.json()["reviewed"] == 0
    assert before.json()["strong_apply_precision"] is None

    unauthenticated = await client.put(
        f"/api/v1/calibration/reviews/{review['id']}",
        json={"human_label": "good_match", "reviewer_notes": "Should fail."},
    )
    assert unauthenticated.status_code == 401

    invalid = await client.put(
        f"/api/v1/calibration/reviews/{review['id']}",
        headers=headers,
        json={"human_label": "excellent", "reviewer_notes": "Invalid label."},
    )
    assert invalid.status_code == 422

    labelled = await client.put(
        f"/api/v1/calibration/reviews/{review['id']}",
        headers=headers,
        json={"human_label": "good_match", "reviewer_notes": "Human reviewed."},
    )
    assert labelled.status_code == 200
    assert labelled.json()["human_label"] == "good_match"
    assert labelled.json()["reviewer_notes"] == "Human reviewed."
    assert labelled.json()["reviewed"] is True
    assert labelled.json()["reviewer_email"] == "reviewer@example.com"
    assert labelled.json()["reviewed_at"] is not None

    persisted = await client.get("/api/v1/calibration/reviews", headers=headers)
    assert persisted.status_code == 200
    assert persisted.json()["reviewed"] == 1
    assert persisted.json()["total"] == 1
    assert persisted.json()["items"][0]["reviewer_notes"] == "Human reviewed."

    updated = await client.put(
        f"/api/v1/calibration/reviews/{review['id']}",
        headers=headers,
        json={"human_label": "strong_match", "reviewer_notes": "Edited review."},
    )
    assert updated.status_code == 200
    assert updated.json()["id"] == review["id"]
    assert updated.json()["human_label"] == "strong_match"
    assert updated.json()["reviewer_notes"] == "Edited review."

    persisted_again = await client.get("/api/v1/calibration/reviews", headers=headers)
    assert persisted_again.json()["total"] == 1
    assert persisted_again.json()["reviewed"] == 1
    assert persisted_again.json()["items"][0]["human_label"] == "strong_match"

    other_auth = await client.post(
        "/api/v1/auth/register",
        json={"email": "other-reviewer@example.com", "password": "VerySecure123!"},
    )
    other_headers = {"Authorization": f"Bearer {other_auth.json()['access_token']}"}
    forbidden = await client.put(
        f"/api/v1/calibration/reviews/{review['id']}",
        headers=other_headers,
        json={"human_label": "reject", "reviewer_notes": "Wrong reviewer."},
    )
    assert forbidden.status_code == 404

    async for session in session_factory():
        database_review = await session.scalar(
            select(CalibrationReview).where(CalibrationReview.id == review["id"])
        )
        assert database_review is not None
        assert database_review.human_label == "strong_match"
        assert database_review.reviewer_notes == "Edited review."
        assert database_review.reviewed_at is not None
        break

    after = await client.get("/api/v1/calibration/evaluation", headers=headers)
    assert after.json()["reviewed"] == 1
    assert after.json()["human_label_distribution"] == {"strong_match": 1}


@pytest.mark.asyncio
async def test_review_ui_contains_persistent_save_feedback(client: AsyncClient) -> None:
    response = await client.get("/app")
    assert response.status_code == 200
    assert '/assets/app.js?v=' in response.text

    javascript = await client.get("/assets/app.js")
    assert javascript.status_code == 200
    assert "human-review-form" in javascript.text
    assert "review-action-status" in javascript.text
    assert "Reviewer:" in javascript.text
    assert "Human review saved successfully" in javascript.text
    assert "Review was not saved:" in javascript.text
    assert "Human review summary" in javascript.text
    assert "EMPLOYER-STATED VACANCY DATA ONLY" not in javascript.text
    assert "Full vacancy — employer source text" in javascript.text
    assert "Reveal Falcon assessment" in javascript.text
    assert '<details class="falcon-assessment">' in javascript.text
    assert 'review.reviewed?`<div class="falcon-comparison">' in javascript.text
    assert '<span class="score">${match.score}%' not in javascript.text
    assert "Create/update 12-job sample" in response.text
    assert "/calibration/validation-sample" in javascript.text
    assert "Existing full live-v1 corpus" in response.text


@pytest.mark.asyncio
async def test_explicit_location_preferences_preserve_unknowns(
    client: AsyncClient,
) -> None:
    auth = await client.post(
        "/api/v1/auth/register",
        json={"email": "location-review@example.com", "password": "VerySecure123!"},
    )
    headers = {"Authorization": f"Bearer {auth.json()['access_token']}"}
    response = await client.put(
        "/api/v1/preferences",
        headers=headers,
        json={
            "home_location": "Croydon",
            "preferred_regions": ["London", "South East England"],
            "search_radius_miles": 40,
            "london_acceptable": True,
            "anywhere_uk_acceptable": False,
            "remote_acceptable": None,
            "hybrid_acceptable": True,
            "relocation_acceptable": None,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["remote_acceptable"] is None
    assert data["relocation_acceptable"] is None
    assert data["anywhere_uk_acceptable"] is False


@pytest.mark.asyncio
async def test_validation_sample_preserves_original_corpus(client: AsyncClient) -> None:
    auth = await client.post(
        "/api/v1/auth/register",
        json={"email": "sample-reviewer@example.com", "password": "VerySecure123!"},
    )
    headers = {"Authorization": f"Bearer {auth.json()['access_token']}"}
    uploaded = await client.post(
        "/api/v1/cvs",
        headers=headers,
        files={
            "file": (
                "cv.txt",
                "Regional Operations Director\n22 years multi-site QSR P&L leadership",
                "text/plain",
            )
        },
    )
    analysis = await client.post(
        f"/api/v1/candidate-intelligence/cvs/{uploaded.json()['id']}/analyze",
        headers=headers,
    )
    user = (await client.get("/api/v1/auth/me", headers=headers)).json()
    session_factory = app.dependency_overrides[get_db_session]
    async for session in session_factory():
        for index in range(15):
            job = DiscoveredJob(
                provider=("deliveroo", "kfc_uk", "wsh_group_uk")[index % 3],
                external_id=f"sample-{index}",
                canonical_key=f"sample-key-{index}",
                canonical_url=f"https://example.com/jobs/sample-{index}",
                title=(
                    "Regional Operations Manager"
                    if index % 3 == 0
                    else "General Manager"
                ),
                company="Live Employer",
                location="London, UK",
                description=(
                    "Lead operational performance across multiple sites and coach "
                    "managers."
                ),
                url=f"https://example.com/jobs/sample-{index}",
                remote=False,
                is_demo=False,
                is_active=True,
                workplace_type="on-site",
                requirements=[],
                source_records=[],
                last_seen_at=datetime.now(UTC),
            )
            session.add(job)
            await session.flush()
            session.add(
                JobMatch(
                    user_id=user["id"],
                    candidate_analysis_id=analysis.json()["id"],
                    job_id=job.id,
                    overall_score=(34, 59, 61, 77, 79)[index % 5],
                    recommendation=("reject", "weak_match", "review", "apply")[
                        index % 4
                    ],
                    occupational_family=(
                        "operations_leadership" if index % 3 == 0 else "retail_site"
                    ),
                    seniority_assessment="manager_lead",
                    strengths=[],
                    gaps=[],
                    mandatory_failures=[],
                    evidence=[],
                    uncertainty=[],
                    recommended_next_action="Review",
                )
            )
        await session.commit()
        break
    original = await client.post(
        "/api/v1/calibration/corpus",
        headers=headers,
        json={
            "candidate_analysis_id": analysis.json()["id"],
            "providers": ["deliveroo", "kfc_uk", "wsh_group_uk"],
            "corpus_version": "live-v1",
        },
    )
    assert original.status_code == 200
    sample = await client.post(
        "/api/v1/calibration/validation-sample",
        headers=headers,
        json={
            "candidate_analysis_id": analysis.json()["id"],
            "providers": ["deliveroo", "kfc_uk", "wsh_group_uk"],
            "corpus_version": "beta-validation-v1",
            "sample_size": 12,
        },
    )
    assert sample.status_code == 200
    assert sample.json()["total"] == 12
    assert all(
        item["falcon_snapshot"]["scope_assessment"]["tier"]
        for item in sample.json()["items"]
    )
    repeated_sample = await client.post(
        "/api/v1/calibration/validation-sample",
        headers=headers,
        json={
            "candidate_analysis_id": analysis.json()["id"],
            "providers": ["deliveroo", "kfc_uk", "wsh_group_uk"],
            "corpus_version": "beta-validation-v1",
            "sample_size": 12,
        },
    )
    assert repeated_sample.status_code == 200
    assert repeated_sample.json()["total"] == 12
    original_after = await client.get(
        "/api/v1/calibration/reviews?corpus_version=live-v1", headers=headers
    )
    assert original_after.json()["total"] == original.json()["total"]
