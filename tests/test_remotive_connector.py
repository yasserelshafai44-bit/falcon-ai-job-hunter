import httpx
import pytest

from app.integrations.remotive import RemotiveConnector


@pytest.mark.asyncio
async def test_remotive_connector_normalizes_jobs() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "jobs": [
                    {
                        "id": 123,
                        "title": "Senior Python Engineer",
                        "company_name": "Example Co",
                        "candidate_required_location": "Worldwide",
                        "description": "Build APIs",
                        "url": "https://example.com/jobs/123",
                        "category": "Software Development",
                        "publication_date": "2026-08-11",
                        "salary": "$100k",
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        connector = RemotiveConnector(client=client)
        jobs = await connector.search(query="python", limit=10)

    assert len(jobs) == 1
    assert jobs[0].source == "remotive"
    assert jobs[0].external_id == "123"
    assert jobs[0].title == "Senior Python Engineer"
    assert jobs[0].remote is True
