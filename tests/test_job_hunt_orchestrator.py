from types import SimpleNamespace

import pytest

from app.services import job_hunt_orchestrator as module


@pytest.mark.asyncio
async def test_prepare_application_runs_end_to_end_to_approval(monkeypatch) -> None:
    calls: list[str] = []

    async def fake_match(**kwargs):
        calls.append("match")
        return SimpleNamespace(id=101)

    async def fake_create(**kwargs):
        calls.append("workflow")
        assert kwargs["job_match_id"] == 101
        return SimpleNamespace(id=202)

    async def fake_generate(**kwargs):
        if str(kwargs["document_type"]).lower().endswith("resume"):
            calls.append("resume")
            return SimpleNamespace(id=303)
        calls.append("cover")
        return SimpleNamespace(id=404)

    async def fake_attach(**kwargs):
        calls.append("attach")
        assert kwargs["resume_document_id"] == 303
        assert kwargs["cover_letter_document_id"] == 404
        return SimpleNamespace(id=202, status="materials_ready")

    async def fake_request(**kwargs):
        calls.append("approval")
        return SimpleNamespace(id=202, status="awaiting_approval")

    monkeypatch.setattr(module, "calculate_and_persist_match", fake_match)
    monkeypatch.setattr(module, "create_workflow", fake_create)
    monkeypatch.setattr(module, "generate_document", fake_generate)
    monkeypatch.setattr(module, "attach_documents", fake_attach)
    monkeypatch.setattr(module, "request_approval", fake_request)

    result = await module.prepare_application(
        session=object(),
        provider=object(),
        user_id=1,
        candidate_analysis_id=2,
        job_id=3,
    )

    assert calls == [
        "match",
        "workflow",
        "resume",
        "cover",
        "attach",
        "approval",
    ]
    assert result.job_match_id == 101
    assert result.workflow_id == 202
    assert result.resume_document_id == 303
    assert result.cover_letter_document_id == 404
    assert "awaiting_approval" in result.status


@pytest.mark.asyncio
async def test_prepare_application_can_skip_cover_letter(monkeypatch) -> None:
    generated_types: list[str] = []

    async def fake_match(**kwargs):
        return SimpleNamespace(id=11)

    async def fake_create(**kwargs):
        return SimpleNamespace(id=22)

    async def fake_generate(**kwargs):
        generated_types.append(str(kwargs["document_type"]))
        return SimpleNamespace(id=33)

    async def fake_attach(**kwargs):
        assert kwargs["cover_letter_document_id"] is None
        return SimpleNamespace(id=22, status="materials_ready")

    async def fake_request(**kwargs):
        return SimpleNamespace(id=22, status="awaiting_approval")

    monkeypatch.setattr(module, "calculate_and_persist_match", fake_match)
    monkeypatch.setattr(module, "create_workflow", fake_create)
    monkeypatch.setattr(module, "generate_document", fake_generate)
    monkeypatch.setattr(module, "attach_documents", fake_attach)
    monkeypatch.setattr(module, "request_approval", fake_request)

    result = await module.prepare_application(
        session=object(),
        provider=object(),
        user_id=1,
        candidate_analysis_id=2,
        job_id=3,
        include_cover_letter=False,
    )

    assert len(generated_types) == 1
    assert result.cover_letter_document_id is None
