import httpx
import pytest
from app.job_providers.base import ProviderError
from app.job_providers.deliveroo import DeliverooProvider
from app.job_providers.role_filter import classify_role


def deliveroo_item(job_id: int, *, location: str = "London - HQ") -> dict:
    return {
        "id": job_id,
        "date_gmt": "2026-08-21T17:10:50",
        "status": "publish",
        "link": f"https://careers.deliveroo.co.uk/role/operations-manager-{job_id}/",
        "title": {"rendered": f"Operations Manager {job_id}"},
        "content": {
            "rendered": (
                "<p>Lead marketplace operations, multi-site P&amp;L and teams.</p>"
            )
        },
        "meta": {"ashby_req_id": f"R{job_id}", "ats_location": location},
    }


@pytest.mark.asyncio
async def test_deliveroo_provider_normalizes_public_careers_response() -> None:
    payload = [
        {
            "id": 320240,
            "date_gmt": "2026-08-21T17:10:50",
            "status": "publish",
            "link": "https://careers.deliveroo.co.uk/role/operations-manager-example/",
            "title": {"rendered": "Operations Manager &#8211; Partner Experience"},
            "content": {"rendered": "<p>Lead marketplace operations and teams.</p>"},
            "meta": {
                "ashby_req_id": "R3714",
                "ats_location": "Manchester - Main Office",
                "ats_remote": False,
            },
        }
    ]

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        jobs = await DeliverooProvider(client).search(keyword="operations")

    assert len(jobs) == 1
    assert jobs[0].provider == "deliveroo"
    assert jobs[0].external_id == "R3714"
    assert jobs[0].company == "Deliveroo"
    assert jobs[0].title == "Operations Manager – Partner Experience"
    assert jobs[0].location == "Manchester - Main Office"
    assert jobs[0].description == "Lead marketplace operations and teams."
    assert jobs[0].posted_at is not None
    assert jobs[0].retrieved_at is not None


@pytest.mark.asyncio
async def test_deliveroo_provider_applies_location_filter() -> None:
    payload = [
        {
            "id": 1,
            "status": "publish",
            "link": "https://careers.deliveroo.co.uk/role/operations-manager-example/",
            "title": {"rendered": "Operations Manager"},
            "content": {"rendered": "Lead operations."},
            "meta": {"ats_location": "Paris - Main Office"},
        }
    ]

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        jobs = await DeliverooProvider(client).search(location="London")
    assert jobs == []


@pytest.mark.parametrize(
    ("title", "description", "eligible"),
    [
        ("Regional Operations Manager", "Lead a region.", True),
        ("Restaurant General Manager", "Own restaurant operations.", True),
        ("Commercial Manager", "Own multi-site P&L and operational performance.", True),
        ("Building Cleaner", "Support daily site operations.", False),
        ("Machine Learning Engineer", "Improve delivery operations.", False),
        ("Business Development Manager", "Lead marketplace sales operations.", False),
    ],
)
def test_pre_score_role_gate_requires_operations_evidence(
    title: str, description: str, eligible: bool
) -> None:
    assert classify_role(title, description).eligible is eligible


@pytest.mark.asyncio
async def test_deliveroo_paginates_each_page_once_and_returns_complete_snapshot() -> (
    None
):
    calls: list[int] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        calls.append(page)
        payload = (
            [deliveroo_item(1), deliveroo_item(2)] if page == 1 else [deliveroo_item(3)]
        )
        return httpx.Response(200, json=payload, headers={"X-WP-TotalPages": "2"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = DeliverooProvider(client)
        provider.page_size = 2
        jobs = await provider.search(limit=20)

    assert calls == [1, 2]
    assert [job.external_id for job in jobs] == ["R1", "R2", "R3"]
    assert provider.complete_snapshot is True


@pytest.mark.asyncio
async def test_deliveroo_rejects_repeated_pagination_page() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[deliveroo_item(1), deliveroo_item(2)],
            headers={"X-WP-TotalPages": "3"},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = DeliverooProvider(client)
        provider.page_size = 2
        with pytest.raises(ProviderError, match="repeated a page"):
            await provider.search(limit=20)
