import httpx
import pytest
from app.job_providers.greene_king import GreeneKingUKProvider


def _detail(job_id: str) -> dict:
    return {
        "id": job_id,
        "name": "Area Manager",
        "postingUrl": f"https://jobs.smartrecruiters.com/GreeneKing/{job_id}-area-manager",
        "releasedDate": "2026-09-01T10:00:00Z",
        "location": {
            "country": "gb",
            "city": "London",
            "fullLocation": "London, United Kingdom",
        },
        "jobAd": {
            "sections": {
                "jobDescription": {
                    "text": (
                        "Lead multiple pubs, general managers, commercial KPIs and P&L."
                    )
                },
                "qualifications": {"text": "Hospitality operations experience."},
            }
        },
    }


@pytest.mark.asyncio
async def test_greene_king_queries_target_families_and_deduplicates() -> None:
    queries: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/postings"):
            queries.append(request.url.params["q"])
            return httpx.Response(
                200,
                json={"totalFound": 1, "content": [{"id": "gk-1"}]},
            )
        return httpx.Response(200, json=_detail("gk-1"))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = GreeneKingUKProvider(
            client=client,
            api_root="https://example.test/v1/companies",
        )
        jobs = await provider.search(limit=100)

    assert queries == list(provider.search_queries)
    assert [job.external_id for job in jobs] == ["gk-1"]
    assert jobs[0].company == "Greene King"
    assert provider.complete_snapshot is True
