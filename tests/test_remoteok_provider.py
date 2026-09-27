import httpx
import pytest
from app.job_providers.base import ProviderError, ProviderRateLimitError
from app.job_providers.remoteok import RemoteOKProvider


@pytest.mark.asyncio
async def test_remoteok_provider_normalizes_jobs() -> None:
    payload = [
        {"legal": "metadata"},
        {
            "id": "123",
            "position": "Operations Manager",
            "company": "Example Co",
            "description": "<p>Lead remote operations</p>",
            "url": "https://remoteok.com/remote-jobs/example-123",
            "location": "UK",
            "tags": ["operations", "hospitality"],
            "salary_min": 60000,
            "salary_max": 80000,
            "date": "2026-08-04T10:00:00+00:00",
        },
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = RemoteOKProvider(client)
        jobs = await provider.search(keyword="operations")

    assert len(jobs) == 1
    assert jobs[0].external_id == "123"
    assert jobs[0].remote is True
    assert jobs[0].description == "Lead remote operations"
    assert jobs[0].is_demo is False
    assert jobs[0].workplace_type == "remote"
    assert jobs[0].url == "https://remoteok.com/remote-jobs/example-123"


@pytest.mark.asyncio
async def test_remoteok_skips_malformed_jobs_without_inventing_fields() -> None:
    payload = [
        {"legal": "metadata"},
        {"id": "missing-title", "company": "Example", "description": "Text"},
        {
            "id": "valid",
            "position": "Manager",
            "company": "Example",
            "description": "Lead a team",
            "url": "https://remoteok.com/remote-jobs/valid",
        },
    ]

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        jobs = await RemoteOKProvider(client).search()

    assert len(jobs) == 1
    assert jobs[0].location == "Location not specified"
    assert jobs[0].salary_min is None
    assert jobs[0].currency is None


@pytest.mark.asyncio
async def test_remoteok_reports_rate_limit_safely() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="upstream details must not leak")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ProviderRateLimitError, match="rate limit"):
            await RemoteOKProvider(client).search()


@pytest.mark.asyncio
async def test_remoteok_rejects_malformed_response_shape() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"jobs": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ProviderError, match="unexpected response shape"):
            await RemoteOKProvider(client).search()
