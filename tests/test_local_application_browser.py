from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.application_adapters.local_smartrecruiters import (
    LocalSmartRecruiters,
    allowed_browser_request,
)
from app.models.application_assistant import CandidateApplicationProfile
from app.services.application_profile import save_application_surname

from tests.conftest import TestSession


@pytest.mark.asyncio
async def test_security_iframe_blocks_without_interacting_with_challenge(tmp_path):
    adapter = LocalSmartRecruiters(None, tmp_path)
    frame = SimpleNamespace(url="https://geo.captcha-delivery.com/captcha/")
    adapter.page = SimpleNamespace(is_closed=lambda: False, frames=[frame])
    assert "human security verification" in await adapter.security_blocker()


@pytest.mark.asyncio
async def test_regular_form_is_not_a_security_challenge(tmp_path):
    adapter = LocalSmartRecruiters(None, tmp_path)
    notice = SimpleNamespace(count=AsyncMock(return_value=0))
    frame = SimpleNamespace(
        url="https://jobs.smartrecruiters.com/oneclick-ui/",
        get_by_text=lambda pattern: notice,
    )
    adapter.page = SimpleNamespace(is_closed=lambda: False, frames=[frame])
    assert await adapter.security_blocker() is None


@pytest.mark.parametrize(
    "url",
    [
        "https://jobs.smartrecruiters.com/oneclick-ui/api/company/65a4f717638a90228e310ec8/applications",
        "https://api.smartrecruiters.com/postings/123/candidates",
        "https://jobs.smartrecruiters.com/oneclick-ui/api/company/65a4f717638a90228e310ec8/attachment/resume/submit",
        "https://example.invalid/submit",
    ],
)
def test_dry_run_denies_application_writes(url):
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        assert allowed_browser_request(method, url) is False


def test_dry_run_only_allows_observed_upload_and_normal_security_requests():
    assert allowed_browser_request(
        "POST",
        "https://jobs.smartrecruiters.com/oneclick-ui/api/company/65a4f717638a90228e310ec8/attachment/resume",
    )
    assert allowed_browser_request(
        "POST",
        "https://jobs.smartrecruiters.com/cdn-cgi/challenge-platform/normal-security-check",
    )
    assert allowed_browser_request("POST", "https://api-js.datadome.co/js/")
    assert not allowed_browser_request(
        "POST",
        "http://jobs.smartrecruiters.com/oneclick-ui/api/company/65a4f717638a90228e310ec8/attachment/resume",
    )


@pytest.mark.asyncio
async def test_application_surname_is_explicit_persistent_and_preserves_other_facts():
    async with TestSession() as session:
        original = {
            "first_name": "Alex",
            "last_name": "Conflicting",
            "work_history": [{"title": "Manager"}],
            "name_conflict": True,
        }
        session.add(CandidateApplicationProfile(user_id=1, data=original))
        await session.commit()
        with pytest.raises(ValueError, match="surname"):
            await save_application_surname(session, 1, " ")
        saved = await save_application_surname(session, 1, "Confirmed Surname")
        assert saved["application_surname"] == saved["last_name"] == "Confirmed Surname"
        assert saved["work_history"] == original["work_history"]
        assert saved["name_conflict"] is False
        session.expire_all()
        stored = await session.get(CandidateApplicationProfile, 1)
        assert stored.data["application_surname"] == "Confirmed Surname"
