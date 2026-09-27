from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.application_adapters.local_smartrecruiters import LocalSmartRecruiters
from app.services.application_profile import enrich_application_facts
from app.services.application_routing import application_route


def test_routing_never_promises_nonexistent_automation():

    for url in (
        "https://jobs.smartrecruiters.com/RaisingCanes/123",
        "https://employer.example/apply",
    ):
        route = application_route(
            SimpleNamespace(url=url, is_active=True, is_demo=False)
        )

        assert route["method"] == "ASSISTED_APPLY"

        assert route["browser_automation_enabled"] is False

        assert route["automated_submission_supported"] is False

    assert (
        application_route(SimpleNamespace(url="javascript:alert(1)"))["method"]
        == "UNAVAILABLE"
    )


@pytest.mark.asyncio
async def test_disabled_browser_cannot_launch_or_fill(tmp_path):

    playwright = SimpleNamespace(chromium=SimpleNamespace(launch=AsyncMock()))

    adapter = LocalSmartRecruiters(playwright, tmp_path)

    with pytest.raises(ValueError, match="disabled"):
        await adapter.open("https://jobs.smartrecruiters.com/RaisingCanes/123")

    with pytest.raises(ValueError, match="disabled"):
        await adapter.populate({}, tmp_path / "cv.docx", "")

    playwright.chromium.launch.assert_not_awaited()


def test_eligibility_needs_literal_source_evidence():

    blank = SimpleNamespace(extracted_text="Manager in London", analysis_data={})

    assert "right_to_work" not in enrich_application_facts({}, blank)

    source = SimpleNamespace(
        extracted_text="Full right to work in the UK | Full UK\nDriving Licence",
        analysis_data={},
    )

    enriched = enrich_application_facts({}, source)

    assert enriched["right_to_work"] == "Full right to work in the UK"

    assert enriched["driving_licence"] == "Full UK Driving Licence"

    assert "notice_period" not in enriched


@pytest.mark.asyncio
async def test_authenticated_assisted_workflow_persists_without_external_calls(
    client, monkeypatch
):

    import httpx

    async def forbidden(*args, **kwargs):

        raise AssertionError("External HTTP must never be used by Assisted Apply")

    # Block outbound HTTP; the test client uses ASGITransport.

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", forbidden)

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

    base = f"/api/v1/application-workflows/{workflow_id}"

    assistant = f"/api/v1/application-assistant/applications/{workflow_id}"

    assert (
        await client.post(assistant + "/continue", headers=headers)
    ).status_code == 422

    assert (
        await client.post(base + "/approve-materials", headers=headers, json={})
    ).status_code == 400

    approved = await client.post(
        base + "/approve-materials",
        headers=headers,
        json={"explicit_review_and_approval": True},
    )

    assert approved.status_code == 200, approved.text

    assert approved.json()["status"] == "approved"

    result = await client.post(assistant + "/continue", headers=headers)

    assert result.status_code == 200, result.text

    pack = result.json()

    assert pack["route"]["method"] == "ASSISTED_APPLY"

    assert pack["external_submission_performed"] is False

    assert "Legal/application surname" in pack["missing_fields"]

    saved = await client.put(
        "/api/v1/application-assistant/profile/fact",
        headers=headers,
        json={"field": "application_surname", "value": "Confirmed"},
    )

    assert saved.status_code == 200, saved.text

    for endpoint in ("/assisted", "/assisted"):
        refreshed = (await client.get(assistant + endpoint, headers=headers)).json()

        assert "Legal/application surname" not in refreshed["missing_fields"]

        assert (
            next(f for f in refreshed["fields"] if f["key"] == "application_surname")[
                "value"
            ]
            == "Confirmed"
        )

    legacy = await client.post(assistant + "/prepare-local", headers=headers)

    assert legacy.json()["state"] == "assisted_apply_required"

    assert (
        await client.get(assistant + "/resume.docx", headers=headers)
    ).status_code == 200

    assert (
        await client.get(assistant + "/cover-letter.txt", headers=headers)
    ).text == pack["cover_letter"]

    assert (await client.get(assistant + "/assisted")).status_code in (401, 403)

    state = (await client.get(base, headers=headers)).json()

    assert state["continued_at"] and state["submitted_at"] is None

    assert (
        await client.post(
            base + "/submitted", headers=headers, json={"confirmed_submitted": True}
        )
    ).status_code == 400
