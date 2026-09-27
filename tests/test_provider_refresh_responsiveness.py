import asyncio
from types import SimpleNamespace

import pytest
from app.services.provider_monitoring import _family_distribution


@pytest.mark.asyncio
async def test_large_refresh_summary_allows_other_requests_to_progress(monkeypatch):
    """A catalogue summary must not monopolise the single production worker."""
    progress = []
    calls = []

    def classify(title, description):
        calls.append(len(progress))
        return "operations_leadership"

    monkeypatch.setattr(
        "app.services.provider_monitoring.classify_occupational_family", classify
    )

    async def other_request():
        while len(calls) < 100:
            progress.append(True)
            await asyncio.sleep(0)

    jobs = [SimpleNamespace(title="Area Manager", description="") for _ in range(100)]
    distribution, _ = await asyncio.gather(_family_distribution(jobs), other_request())
    assert distribution == {"operations_leadership": 100}
    assert calls[-1] > calls[0], "Another request must progress before summary finishes"
