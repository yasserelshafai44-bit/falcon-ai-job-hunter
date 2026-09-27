import httpx
import pytest
from app.job_providers.base import ProviderError
from app.job_providers.kfc import KFCUKProvider


def kfc_job(
    job_id: str,
    *,
    title: str = "Area Coach",
    city: str = "London",
    country: str = "United Kingdom",
) -> dict:
    return {
        "id": int(job_id),
        "ats_id": job_id,
        "job_title": title,
        "description_html": (
            "<p>Lead multi-site restaurant operations, regional performance, "
            "P&amp;L, KPIs and coach managers.</p>"
        ),
        "job_url": f"https://careers.kfc.co.uk/jobs/area-coach.{job_id}",
        "employment_type": "full time",
        "location_city": city,
        "location_country": country,
        "location_postcode": "SW1A 1AA" if city == "London" else "",
        "salary_display": "£55K - £65K per annum",
        "ats_created_timestamp_utc": "2026-08-20 00:00:00",
        "closing_date": "2026-09-20 00:00:00",
    }


@pytest.mark.asyncio
async def test_kfc_provider_normalizes_relevant_uk_leadership_jobs() -> None:
    payload = {
        "results_total": 4,
        "jobs": [
            kfc_job("100"),
            kfc_job("100"),
            kfc_job("101", title="Cook"),
            kfc_job("102", city="Dublin", country="Ireland"),
        ],
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = KFCUKProvider(client)
        jobs = await provider.search()

    assert len(jobs) == 1
    assert jobs[0].provider == "kfc_uk"
    assert jobs[0].external_id == "100"
    assert jobs[0].company == "KFC UK"
    assert jobs[0].location == "London, United Kingdom, SW1A 1AA"
    assert jobs[0].salary_min == 55_000
    assert jobs[0].salary_max == 65_000
    assert jobs[0].currency == "GBP"
    assert jobs[0].posted_at is not None
    assert jobs[0].expires_at is not None
    assert provider.complete_snapshot is True


@pytest.mark.asyncio
async def test_kfc_failure_is_reported_safely() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ProviderError, match="HTTP 503"):
            await KFCUKProvider(client).search()
