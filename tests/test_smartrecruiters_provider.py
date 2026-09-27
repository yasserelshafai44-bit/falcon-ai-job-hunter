import json

import httpx
import pytest
from app.job_providers.base import ProviderError
from app.job_providers.raising_canes import RaisingCanesUKProvider


def detail(
    job_id: str,
    *,
    title: str = "Area Leader of Restaurants (Operations Manager)",
    country: str = "gb",
    city: str = "London",
) -> dict:
    return {
        "id": job_id,
        "name": title,
        "postingUrl": f"https://jobs.smartrecruiters.com/RaisingCanes/{job_id}-area-leader",
        "releasedDate": "2026-09-01T10:00:00Z",
        "location": {
            "country": country,
            "city": city,
            "region": "England",
            "fullLocation": f"{city}, England, {country.upper()}",
        },
        "typeOfEmployment": {"label": "Full-time"},
        "jobAd": {
            "sections": {
                "companyDescription": {"text": "Raising Cane's operates restaurants."},
                "jobDescription": {
                    "text": (
                        "Lead multiple restaurants, coach managers and own P&L and "
                        "operational performance."
                    )
                },
                "qualifications": {
                    "text": (
                        "<ul><li>Five years multi-unit leadership</li>"
                        "<li>UK driving licence</li></ul>"
                    )
                },
                "additionalInformation": {
                    "text": "Travel throughout the region is required."
                },
            }
        },
    }


@pytest.mark.asyncio
async def test_smartrecruiters_paginates_and_preserves_full_provenance() -> None:
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.url.path, request.url.query.decode()))
        if request.url.path.endswith("/postings"):
            offset = int(request.url.params["offset"])
            content = [{"id": str(offset + 1)}] if offset < 2 else []
            return httpx.Response(200, json={"totalFound": 2, "content": content})
        return httpx.Response(200, json=detail(request.url.path.rsplit("/", 1)[-1]))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = RaisingCanesUKProvider(
            client=client, api_root="https://example.test/v1/companies"
        )
        provider.page_size = 1
        jobs = await provider.search(limit=100)

    assert [job.external_id for job in jobs] == ["1", "2"]
    assert jobs[0].provider == "raising_canes_uk"
    assert jobs[0].company == "Raising Cane's UK"
    assert jobs[0].url.startswith("https://jobs.smartrecruiters.com/RaisingCanes/")
    assert jobs[0].requirements == (
        "Five years multi-unit leadership",
        "UK driving licence",
    )
    assert jobs[0].posted_at is not None and jobs[0].retrieved_at is not None
    assert provider.complete_snapshot is True
    list_calls = [query for path, query in calls if path.endswith("/postings")]
    assert len(list_calls) == 2
    assert "offset=0" in list_calls[0] and "offset=1" in list_calls[1]
    assert all("country=gb" in query for query in list_calls)


@pytest.mark.asyncio
async def test_smartrecruiters_rejects_non_uk_but_retains_all_occupations() -> None:
    details = {
        "1": detail("1", country="us"),
        "2": detail("2", title="Software Engineering Manager"),
        "3": detail("3", title="Restaurant General Manager", city="Manchester"),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/postings"):
            return httpx.Response(
                200, json={"totalFound": 3, "content": [{"id": key} for key in details]}
            )
        return httpx.Response(200, json=details[request.url.path.rsplit("/", 1)[-1]])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        jobs = await RaisingCanesUKProvider(
            client=client, api_root="https://example.test/v1/companies"
        ).search()

    assert [job.external_id for job in jobs] == ["2", "3"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [{}, {"totalFound": "bad", "content": []}, {"totalFound": 1, "content": [{}]}],
)
async def test_smartrecruiters_rejects_malformed_list_response(payload: dict) -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=json.dumps(payload))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = RaisingCanesUKProvider(
            client=client, api_root="https://example.test/v1/companies"
        )
        with pytest.raises(ProviderError):
            await provider.search()
    assert provider.complete_snapshot is False


@pytest.mark.asyncio
async def test_cached_detail_requires_same_release_and_current_list_membership():
    current = detail("1")
    rows = [current]
    detail_calls = []

    def handler(request):
        if request.url.path.endswith("/postings"):
            return httpx.Response(200, json={"totalFound": len(rows), "content": rows})
        detail_calls.append(request.url.path)
        return httpx.Response(200, json=current)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = RaisingCanesUKProvider(client=client)
        first = await provider.search()
        provider.cached_jobs = {first[0].external_id: first[0]}
        assert len(await provider.search()) == 1
        assert len(detail_calls) == 1
        current["releasedDate"] = "2026-09-28T10:00:00Z"
        await provider.search()
        assert len(detail_calls) == 2
        rows.clear()
        assert await provider.search() == []
        assert provider.complete_snapshot and provider.authoritative_empty


@pytest.mark.asyncio
async def test_smartrecruiters_detail_failure_does_not_mark_complete() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/postings"):
            return httpx.Response(200, json={"totalFound": 1, "content": [{"id": "1"}]})
        return httpx.Response(503, json={"message": "unavailable"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = RaisingCanesUKProvider(
            client=client, api_root="https://example.test/v1/companies"
        )
        with pytest.raises(ProviderError, match="HTTP 503"):
            await provider.search()
    assert provider.complete_snapshot is False


@pytest.mark.asyncio
async def test_smartrecruiters_repeated_page_is_rejected() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"totalFound": 2, "content": [{"id": "same"}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = RaisingCanesUKProvider(
            client=client, api_root="https://example.test/v1/companies"
        )
        provider.page_size = 1
        with pytest.raises(ProviderError, match="repeated"):
            await provider.search()
