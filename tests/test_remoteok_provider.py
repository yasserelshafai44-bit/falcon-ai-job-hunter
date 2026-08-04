import httpx
import pytest

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
            "url": "https://example.com/jobs/123",
            "location": "UK",
            "tags": ["operations", "hospitality"],
            "salary_min": 60000,
            "salary_max": 80000,
            "date": "2026-08-04T10:00:00+00:00",
        },
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as client:
        provider = RemoteOKProvider(client)
        jobs = await provider.search(keyword="operations")

    assert len(jobs) == 1
    assert jobs[0].external_id == "123"
    assert jobs[0].remote is True
    assert jobs[0].description == "Lead remote operations"
