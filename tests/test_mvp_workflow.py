import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_local_end_to_end_workflow(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    registered = await client.post(
        "/api/v1/auth/register",
        json={"email": "mvp@example.com", "password": "VerySecure123!"},
    )
    assert registered.status_code == 201
    headers = {
        "Authorization": f"Bearer {registered.json()['access_token']}",
    }
    providers = await client.get("/api/v1/jobs/providers", headers=headers)
    assert providers.status_code == 200
    assert providers.json()[0]["id"] == "remoteok"
    assert providers.json()[0]["kind"] == "real"
    assert providers.json()[0]["credentials_required"] is False
    assert providers.json()[1]["kind"] == "demo"

    uploaded = await client.post(
        "/api/v1/cvs",
        headers=headers,
        files={
            "file": (
                "resume.txt",
                b"ALEX EXAMPLE\nRegional Operations Manager\n"
                b"London, UK | alex@example.com\nPROFESSIONAL SUMMARY\n"
                b"Operations leader with 12+ years of experience in hospitality.\n"
                b"CORE SKILLS\nMulti-site operations and team leadership.\n"
                b"Managed delivery operations and improved margin by 12%.\n"
                b"Experienced in KPI management, food safety and supplier management.\n"
                b"EDUCATION\nExample College - Operations Certificate\n"
                b"LANGUAGES\nEnglish",
                "text/plain",
            )
        },
    )
    assert uploaded.status_code == 201

    analysed = await client.post(
        f"/api/v1/candidate-intelligence/cvs/{uploaded.json()['id']}/analyze",
        headers=headers,
    )
    assert analysed.status_code == 200
    analysis_id = analysed.json()["id"]
    assert analysed.json()["analysis"]["skills"]
    assert analysed.json()["analysis"]["professional_summary"] != "Alex Example"
    assert analysed.json()["analysis"]["full_name"]["source_text"] == "ALEX EXAMPLE"

    manual = await client.put(
        "/api/v1/profile",
        headers=headers,
        json={
            "full_name": "Manual Name",
            "email": "mvp@example.com",
            "location": "Manual Location",
            "years_experience": 3,
            "profile_data": {},
        },
    )
    assert manual.status_code == 200
    accepted = await client.post(
        f"/api/v1/candidate-intelligence/{analysis_id}/apply-profile",
        headers=headers,
        json={"fields": ["years_experience", "professional_summary", "skills"]},
    )
    assert accepted.status_code == 200
    assert accepted.json()["full_name"] == "Manual Name"
    assert accepted.json()["location"] == "Manual Location"
    assert accepted.json()["years_experience"] == 12
    assert accepted.json()["profile_data"]["accepted_cv_enrichment"][
        "professional_summary"
    ]["source_text"]

    synced = await client.post(
        "/api/v1/jobs/sync",
        headers=headers,
        json={
            "keyword": "Operations Manager",
            "location": "London",
            "providers": ["local"],
            "limit_per_provider": 3,
        },
    )
    assert synced.status_code == 200
    assert synced.json()["inserted"] == 3

    jobs = await client.get("/api/v1/jobs", headers=headers)
    assert jobs.status_code == 200
    job_id = jobs.json()["items"][0]["id"]

    matched = await client.post(
        f"/api/v1/matches/jobs/{job_id}/score",
        headers=headers,
        json={"candidate_analysis_id": analysis_id},
    )
    assert matched.status_code == 200
    assert 0 <= matched.json()["overall_score"] <= 100
    assert matched.json()["evidence"]

    batched = await client.post(
        "/api/v1/matches/jobs/score-batch",
        headers=headers,
        json={"candidate_analysis_id": analysis_id, "job_ids": [job_id]},
    )
    assert batched.status_code == 200
    assert batched.json()[0]["job_id"] == job_id

    documents = []
    for endpoint in ("resume", "cover-letter"):
        generated = await client.post(
            f"/api/v1/{endpoint}/generate",
            headers=headers,
            json={
                "candidate_analysis_id": analysis_id,
                "job_id": job_id,
                "tone": "professional",
                "max_words": 350,
            },
        )
        assert generated.status_code == 200
        assert generated.json()["content"]
        content = generated.json()["content"]
        assert "improved margin by 12%" in content
        assert "Verified achievement included" not in content
        assert generated.json()["provider"] == "evidence_grounded"
        documents.append(generated.json()["id"])

    workflow = await client.post(
        "/api/v1/application-workflows",
        headers=headers,
        json={"job_match_id": matched.json()["id"]},
    )
    workflow_id = workflow.json()["id"]
    duplicate = await client.post(
        "/api/v1/application-workflows",
        headers=headers,
        json={"job_match_id": matched.json()["id"]},
    )
    assert duplicate.json()["id"] == workflow_id

    missing_review = await client.get(
        f"/api/v1/application-workflows/{workflow_id}/review",
        headers=headers,
    )
    assert missing_review.status_code == 404
    assert "resume is missing" in missing_review.json()["error"]["message"]

    attached = await client.post(
        f"/api/v1/application-workflows/{workflow_id}/documents",
        headers=headers,
        json={
            "resume_document_id": documents[0],
            "cover_letter_document_id": documents[1],
        },
    )
    assert attached.json()["status"] == "materials_ready"

    review = await client.get(
        f"/api/v1/application-workflows/{workflow_id}/review",
        headers=headers,
    )
    assert review.status_code == 200
    assert review.json()["job"]["title"] == jobs.json()["items"][0]["title"]
    assert review.json()["job"]["company"] == jobs.json()["items"][0]["company"]
    assert review.json()["resume"]["content"]
    assert review.json()["cover_letter"]["content"]
    assert review.json()["original_cv_evidence"]["skills"]
    assert review.json()["resume"]["change_summary"]
    assert review.json()["status_history"]
    old_resume = review.json()["resume"]["content"]
    regenerated = await client.post(
        f"/api/v1/application-workflows/{workflow_id}/regenerate-materials",
        headers=headers,
    )
    assert regenerated.status_code == 200
    assert regenerated.json()["id"] == workflow_id
    assert regenerated.json()["status"] == "materials_ready"
    assert regenerated.json()["reviewed_at"] is None
    assert regenerated.json()["submitted_at"] is None
    refreshed_review = await client.get(
        f"/api/v1/application-workflows/{workflow_id}/review", headers=headers
    )
    assert refreshed_review.json()["resume"]["content"] == old_resume
    history = await client.get("/api/v1/generation/history", headers=headers)
    assert len(history.json()["items"]) == 4
    assert any(item["id"] == documents[0] for item in history.json()["items"])
    documents = [
        regenerated.json()["resume_document_id"],
        regenerated.json()["cover_letter_document_id"],
    ]
    from app.services import application_materials
    from app.services.document_generation import GenerationInputError

    original_generate = application_materials.generate_document

    async def fail_cover(**kwargs):
        if kwargs["document_type"].value == "cover_letter":
            raise GenerationInputError("Cover-letter generation failed")
        return await original_generate(**kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(application_materials, "generate_document", fail_cover)
        failed = await client.post(
            f"/api/v1/application-workflows/{workflow_id}/regenerate-materials",
            headers=headers,
        )
    assert failed.status_code == 422
    unchanged = await client.get(
        f"/api/v1/application-workflows/{workflow_id}", headers=headers
    )
    assert unchanged.json()["resume_document_id"] == documents[0]
    history = await client.get("/api/v1/generation/history", headers=headers)
    assert len(history.json()["items"]) == 4
    review_match = review.json()["match"]
    rendered_explanations = review_match["strengths"] + [
        item["explanation"] for item in review_match["evidence"]
    ]
    assert len(rendered_explanations) == len(set(rendered_explanations))
    final_gaps = (
        review_match["gaps"]
        + review_match["mandatory_failures"]
        + review_match["uncertainty"]
    )
    assert sum("Location" in item for item in final_gaps) == 1
    assert any("Salary" in item for item in review_match["uncertainty"])

    other = await client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "password": "VerySecure123!"},
    )
    other_headers = {
        "Authorization": f"Bearer {other.json()['access_token']}",
    }
    forbidden = await client.get(
        f"/api/v1/application-workflows/{workflow_id}/review",
        headers=other_headers,
    )
    assert forbidden.status_code == 404
    forbidden_regeneration = await client.post(
        f"/api/v1/application-workflows/{workflow_id}/regenerate-materials",
        headers=other_headers,
    )
    assert forbidden_regeneration.status_code == 422

    premature = await client.post(
        f"/api/v1/application-workflows/{workflow_id}/request-approval",
        headers=headers,
    )
    assert premature.status_code == 400
    assert "Review" in premature.json()["error"]["message"]

    reviewed = await client.post(
        f"/api/v1/application-workflows/{workflow_id}/reviewed",
        headers=headers,
    )
    assert reviewed.json()["reviewed_at"]

    revised = await client.patch(
        f"/api/v1/generation/{documents[0]}",
        headers=headers,
        json={"content": "User-reviewed factual resume draft."},
    )
    assert revised.status_code == 200
    revised_cover = await client.patch(
        f"/api/v1/generation/{documents[1]}",
        headers=headers,
        json={"content": "User-edited factual cover letter."},
    )
    assert revised_cover.status_code == 200
    reset_review = await client.get(
        f"/api/v1/application-workflows/{workflow_id}", headers=headers
    )
    assert reset_review.json()["reviewed_at"] is None

    await client.post(
        f"/api/v1/application-workflows/{workflow_id}/reviewed",
        headers=headers,
    )
    requested = await client.post(
        f"/api/v1/application-workflows/{workflow_id}/request-approval",
        headers=headers,
    )
    assert requested.json()["status"] == "awaiting_approval"
    approved = await client.post(
        f"/api/v1/application-workflows/{workflow_id}/approve",
        headers=headers,
        json={"notes": "Reviewed locally"},
    )
    assert approved.json()["status"] == "approved"
    assert approved.json()["submitted_at"] is None
    unconfirmed = await client.post(
        f"/api/v1/application-workflows/{workflow_id}/submitted",
        headers=headers,
        json={},
    )
    assert unconfirmed.status_code == 400
    fresh = await client.post(
        f"/api/v1/application-workflows/{workflow_id}/regenerate-materials",
        headers=headers,
    )
    assert fresh.status_code == 200
    assert fresh.json()["status"] == "materials_ready"
    assert fresh.json()["reviewed_at"] is None
    assert fresh.json()["submitted_at"] is None

    cvs = await client.get("/api/v1/cvs", headers=headers)
    assert len(cvs.json()) == 1


@pytest.mark.asyncio
async def test_jobs_require_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/jobs")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_frontend_is_served(client: AsyncClient) -> None:
    response = await client.get("/app")
    assert response.status_code == 200
    assert "Falcon AI Job Hunter" in response.text

    script = await client.get("/assets/app.js")
    assert script.status_code == 200
    assert "await request('/auth/me')" in script.text
    assert "restoreCandidateAnalysis" in script.text
    assert "Unable to refresh and rank jobs:" in script.text
    assert "Prepare failed:" in script.text
    assert "Review application" in script.text
    assert "Original CV evidence" in script.text
    assert "evidenceList(matchEvidenceItems(m))" in script.text
    assert "evidenceList(m.strengths)}${evidenceList(m.evidence)" not in script.text
    assert "evidenceList(matchGapItems(m))" in script.text
    assert "data-job-id" in script.text
    assert "View original vacancy" in script.text
    assert "Best matches filters" in response.text
    assert "All verified direct employers" in response.text
    assert "Deliveroo + KFC" not in response.text
    assert "resolve_provider_selection" not in script.text
    assert "providers=selectedProviders(selected)" in script.text
    assert "const refreshedProviders=sync.providers_requested" in script.text
    assert response.headers["cache-control"] == "no-store, max-age=0"
    assert "Final match-quality check" in response.text
    assert "Employer coverage" in response.text
    assert "Why this career fit" in script.text
    assert "Live vacancies" in script.text
    assert "previously verified" in script.text
    assert "Role fit" in script.text
    assert "Mandatory requirements" in script.text
    assert "Remote OK — REAL vacancies" in response.text
    assert "Local fixtures — DEMO only" in response.text
    assert "onclick=" not in script.text
