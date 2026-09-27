import pytest
from app.commands.finish_beta import verify_preserved
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_prepare_review_approve_and_manual_handoff(client: AsyncClient) -> None:
    account = await client.post(
        "/api/v1/auth/register",
        json={"email": "beta-test@example.com", "password": "VerySecure123!"},
    )
    headers = {"Authorization": f"Bearer {account.json()['access_token']}"}
    source = (
        "ALEX EXAMPLE\nRegional Restaurant Manager\nPROFESSIONAL SUMMARY\n"
        "Restaurant operations leader with 14 years of experience in multi-site QSR.\n"
        "CORE SKILLS\nManaged 18 restaurants with full P&L accountability.\n"
        "Led 180 colleagues and developed six restaurant managers.\n"
        "Reduced labour costs by 8% while maintaining food safety standards.\n"
        "Managed delivery operations handling 2,400 daily orders.\n"
        "EDUCATION\nDiploma in Hospitality Management.\n"
    )
    cv = await client.post(
        "/api/v1/cvs",
        headers=headers,
        files={"file": ("evidence.txt", source.encode(), "text/plain")},
    )
    analysis = await client.post(
        f"/api/v1/candidate-intelligence/cvs/{cv.json()['id']}/analyze",
        headers=headers,
    )
    analysis_id = analysis.json()["id"]
    imported = await client.post(
        "/api/v1/jobs/manual",
        headers=headers,
        json={
            "candidate_analysis_id": analysis_id,
            "source_url": "https://employer.example/jobs/area-manager",
            "employer": "Example Restaurant Employer",
            "title": "Area Restaurant Manager",
            "location": "London",
            "description": "Lead multiple restaurants with full P&L accountability. "
            "Develop restaurant managers, manage financial performance "
            "and uphold food safety. "
            "Take responsibility for budget planning and regional operations.",
            "requirements": ["Multi-site restaurant leadership"],
            "workplace_type": "on-site",
        },
    )
    assert imported.status_code == 200, imported.text
    matched = imported.json()["match"]
    prepared = await client.post(
        "/api/v1/application-workflows/prepare",
        headers=headers,
        json={"job_match_id": matched["id"]},
    )
    assert prepared.status_code == 200, prepared.text
    workflow = prepared.json()
    workflow_id = workflow["id"]
    assert workflow["status"] == "materials_ready"
    assert workflow["resume_document_id"] and workflow["cover_letter_document_id"]
    review_url = f"/api/v1/application-workflows/{workflow_id}"
    review = (await client.get(review_url + "/review", headers=headers)).json()
    assert "18 restaurants" in review["resume"]["content"]
    assert "Example Restaurant Employer" in review["cover_letter"]["content"]
    assert review["job"]["url"] == "https://employer.example/jobs/area-manager"
    assert review["automated_submission_supported"] is False
    assert review["unanswered_employer_questions"] == []
    again = await client.post(
        "/api/v1/application-workflows/prepare",
        headers=headers,
        json={"job_match_id": matched["id"]},
    )
    assert again.json()["resume_document_id"] == workflow["resume_document_id"]
    premature = await client.post(review_url + "/request-approval", headers=headers)
    assert premature.status_code == 400
    assert (
        await client.post(review_url + "/reviewed", headers=headers)
    ).status_code == 200
    requested = await client.post(review_url + "/request-approval", headers=headers)
    assert requested.json()["status"] == "awaiting_approval"

    # Editing either material invalidates the prior review and approval request.
    cover_id = workflow["cover_letter_document_id"]
    revised = await client.patch(
        f"/api/v1/generation/{cover_id}",
        headers=headers,
        json={"content": review["cover_letter"]["content"] + "\nThank you."},
    )
    assert revised.status_code == 200
    assert (
        revised.json()["metadata_json"]["revisions"][0]["content"]
        == review["cover_letter"]["content"]
    )
    state = (await client.get(review_url, headers=headers)).json()
    assert state["status"] == "materials_ready" and state["reviewed_at"] is None
    assert (
        await client.post(review_url + "/approve", headers=headers, json={})
    ).status_code == 400
    await client.post(review_url + "/reviewed", headers=headers)
    await client.post(review_url + "/request-approval", headers=headers)
    approved = await client.post(review_url + "/approve", headers=headers, json={})
    assert approved.json()["status"] == "approved"
    assert approved.json()["submitted_at"] is None
    # A boolean, URL, or alternate outcome route is not employer confirmation.
    unsupported = await client.post(
        review_url + "/submitted",
        headers=headers,
        json={
            "confirmed_submitted": True,
            "external_application_url": "https://employer.example/confirmation",
        },
    )
    assert unsupported.status_code == 400
    bypass = await client.post(
        review_url + "/outcome", headers=headers, json={"status": "submitted"}
    )
    assert bypass.status_code == 400
    state = (await client.get(review_url, headers=headers)).json()
    assert state["status"] == "approved" and state["submitted_at"] is None


def test_preservation_detects_modified_or_deleted_existing_rows() -> None:
    before = {"users": {"[1]": "original"}, "generated_documents": {"[1]": "old"}}
    verify_preserved(
        before,
        {
            "users": {"[1]": "original"},
            "generated_documents": {"[1]": "old", "[2]": "new"},
        },
    )
    with pytest.raises(RuntimeError, match="Preservation check"):
        verify_preserved(before, {"users": {}, "generated_documents": {"[1]": "old"}})
    with pytest.raises(RuntimeError, match="Preservation check"):
        verify_preserved(before, {"users": {"[1]": "changed"}})
