import asyncio
import threading
from types import SimpleNamespace

import pytest
from app.services.provider_monitoring import _family_distribution


@pytest.mark.asyncio
async def test_large_refresh_summary_allows_other_requests_to_progress(monkeypatch):
    """A catalogue summary must not monopolise the single production worker."""
    progress = []
    calls = []
    midpoint, released = threading.Event(), threading.Event()

    def classify(title, description):
        calls.append(len(progress))
        if len(calls) == 20:
            midpoint.set()
            assert released.wait(timeout=2)
        return "operations_leadership"

    monkeypatch.setattr(
        "app.services.provider_monitoring.classify_occupational_family", classify
    )

    async def other_request():
        while not midpoint.is_set():
            await asyncio.sleep(0)
        progress.append(True)
        released.set()

    jobs = [
        SimpleNamespace(title=f"Area Manager {i}", description="") for i in range(100)
    ]
    distribution, _ = await asyncio.gather(_family_distribution(jobs), other_request())
    assert distribution == {"operations_leadership": 100}
    assert calls[-1] > calls[0], "Another request must progress before summary finishes"


@pytest.mark.asyncio
async def test_repeated_descriptions_count_all_jobs_without_repeating_cpu_work(
    monkeypatch,
):
    calls = []

    def classify(title, description):
        calls.append((title, description))
        return "culinary"

    monkeypatch.setattr(
        "app.services.provider_monitoring.classify_occupational_family", classify
    )
    jobs = [SimpleNamespace(title="Chef", description="same published advert")] * 100
    assert await _family_distribution(jobs) == {"culinary": 100}
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_even_one_slow_description_does_not_block_the_web_event_loop(monkeypatch):
    started, released = threading.Event(), threading.Event()

    def classify(title, description):
        started.set()
        assert released.wait(timeout=2), "Event loop blocked by classification"
        return "unknown"

    monkeypatch.setattr(
        "app.services.provider_monitoring.classify_occupational_family", classify
    )

    async def health_request():
        while not started.is_set():
            await asyncio.sleep(0)
        released.set()

    result, _ = await asyncio.gather(
        _family_distribution([SimpleNamespace(title="Unknown", description="")]),
        health_request(),
    )
    assert result == {"unknown": 1}
