from datetime import UTC, datetime, timedelta
from io import BytesIO
from types import SimpleNamespace

import pytest
from app.application_adapters.smartrecruiters import SmartRecruitersAdapter
from app.models.application_assistant import ApplicationAssistantSession
from app.services import application_assistant as service
from app.services.application_files import resume_docx
from app.services.application_profile import extract_reusable_facts
from docx import Document
from sqlalchemy import select

from tests.conftest import TestSession


def profile():
    return {
        "first_name": "Alex",
        "last_name": "Example",
        "email": "alex@example.com",
        "phone": "+441234567890",
        "city": "London",
        "name_conflict": False,
        "work_history": [
            {
                "title": "Manager",
                "company": "Example",
                "location": "UK",
                "source_text": "Manager — Example | Jan 2020 – Present",
            }
        ],
        "education": [{"description": "University — Law (2000)"}],
    }


def test_docx_preserves_text_and_is_byte_stable():
    text = "Alex Example\nProfessional Summary\nExperienced manager.\n- Led 18 teams."
    content = resume_docx(text)
    assert content == resume_docx(text)
    assert [p.text for p in Document(BytesIO(content)).paragraphs] == [
        "Alex Example",
        "Professional Summary",
        "Experienced manager.",
        "Led 18 teams.",
    ]


def test_profile_reuses_source_facts_and_detects_conflicting_name():
    candidate = SimpleNamespace(
        full_name="Alex Example", email="a@example.com", phone=None, location=None
    )
    analysis = SimpleNamespace(
        id=1,
        extracted_text=(
            "ALEX OTHER\nLondon, UK | +44 1234 567890\nWORK HISTORY\n"
            "Manager — Example\nLondon | Jan 2020 – Present\nEDUCATION\n"
            "• University — Law (2000)\nLANGUAGES\nEnglish"
        ),
    )
    facts = extract_reusable_facts(candidate, analysis)
    assert facts["name_conflict"]
    assert facts["phone"] == "+44 1234 567890"
    assert len(facts["work_history"]) == len(facts["education"]) == 1


def test_adapter_stages_supported_facts_but_never_guesses_questions():
    questions = [
        {
            "id": str(i),
            "label": label,
            "fields": [{"id": "value", "type": "INPUT_TEXT", "required": True}],
        }
        for i, label in enumerate(
            [
                "Email address",
                "Do you need sponsorship?",
                "Ethnicity",
                "Accept privacy policy?",
            ]
        )
    ]
    result = SmartRecruitersAdapter().populate(profile(), {"questions": questions})
    assert result["fields"]["experience"][0]["company"] == "Example"
    assert result["fields"]["education"]
    assert result["questions"][0]["answer"] == "alex@example.com"
    assert all(item["answer"] is None for item in result["questions"][1:])
    assert not result["employer_form_populated"] and not result["resume_uploaded"]
    assert len(result["unresolved"]) == 3


@pytest.mark.asyncio
async def test_missing_credential_does_not_probe_protected_api(monkeypatch):
    import app.application_adapters.smartrecruiters as module

    monkeypatch.setattr(
        module,
        "get_settings",
        lambda: SimpleNamespace(
            smartrecruiters_application_token=None,
            smartrecruiters_application_company=None,
        ),
    )
    result = await SmartRecruitersAdapter().inspect(
        "https://jobs.smartrecruiters.com/RaisingCanes/744000140850342-area-leader"
    )
    assert result["status"] == "blocked" and result["questions"] is None


@pytest.mark.asyncio
async def test_final_gate_is_separate_stale_safe_and_never_submits(monkeypatch):
    async def fixture_inputs(*args):
        return (None, None, None, None, None, "original")

    monkeypatch.setattr(service, "inputs", fixture_inputs)
    snapshot = {
        "configuration": {"status": "retrieved"},
        "unresolved": [],
        "dry_run": True,
    }
    async with TestSession() as session:
        record = ApplicationAssistantSession(
            id="test",
            user_id=1,
            workflow_id=21,
            state="review_required",
            snapshot=snapshot,
            snapshot_digest=service.digest(snapshot),
            input_digest="original",
        )
        session.add(record)
        await session.commit()
        with pytest.raises(ValueError, match="Final submission approval"):
            await service.dry_run_submit(session, 1, "test", record.snapshot_digest)
        with pytest.raises(ValueError, match="Explicit"):
            await service.final_approve(
                session, 1, "test", record.snapshot_digest, False
            )
        with pytest.raises(ValueError, match="changed"):
            await service.final_approve(session, 1, "test", "x" * 64, True)
        view = await service.final_approve(
            session, 1, "test", record.snapshot_digest, True
        )
        assert view["state"] == "final_approved_dry_run"
        record.final_approved_at = datetime.now(UTC) - timedelta(minutes=6)
        await session.commit()
        with pytest.raises(ValueError, match="expired"):
            await service.dry_run_submit(session, 1, "test", record.snapshot_digest)
        record.final_approved_at = datetime.now(UTC)
        await session.commit()
        result = await service.dry_run_submit(
            session, 1, "test", record.snapshot_digest
        )
        assert result["external_submission_performed"] is False
        with pytest.raises(ValueError, match="Final submission approval"):
            await service.dry_run_submit(session, 1, "test", record.snapshot_digest)
        with pytest.raises(ValueError, match="not found"):
            await service.get_session(session, 2, "test")


@pytest.mark.asyncio
async def test_unknown_configuration_cannot_receive_final_approval():
    snapshot = {
        "configuration": {"status": "blocked"},
        "unresolved": ["Unknown employer questions"],
    }
    async with TestSession() as session:
        record = ApplicationAssistantSession(
            id="blocked",
            user_id=1,
            workflow_id=21,
            state="blocked",
            snapshot=snapshot,
            snapshot_digest=service.digest(snapshot),
            input_digest="x",
        )
        session.add(record)
        await session.commit()
        with pytest.raises(ValueError, match="Resolve"):
            await service.final_approve(
                session, 1, "blocked", record.snapshot_digest, True
            )
        record = await session.scalar(select(ApplicationAssistantSession))
        assert record.final_approved_at is None
