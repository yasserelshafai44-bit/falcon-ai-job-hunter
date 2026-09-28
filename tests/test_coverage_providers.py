import json
from datetime import UTC, datetime

import httpx
import pytest
from app.job_providers.base import ProviderError
from app.job_providers.dominos import DominosUKProvider
from app.job_providers.lever import LeverUKProvider


def posting(identifier="1", country="GB", title="Software Engineer"):
    return {
        "id": identifier,
        "text": title,
        "country": country,
        "categories": {"location": "London", "allLocations": ["London"]},
        "hostedUrl": f"https://jobs.lever.co/example/{identifier}",
        "descriptionPlain": "A genuine published specialist vacancy.",
        "lists": [{"text": "Requirements", "content": "<p>Engineering degree</p>"}],
        "workplaceType": "hybrid",
    }


def test_lever_explicit_non_uk_country_overrides_ambiguous_primary_city():
    provider = LeverUKProvider(name="example", employer="Example", site="example")
    assert provider._normalize(posting(country="CA")) is None
    alternative = posting(country="BE")
    alternative["categories"] = {
        "location": "Ghent",
        "allLocations": ["Ghent", "London"],
    }
    assert provider._normalize(alternative).location == "London, United Kingdom"


@pytest.mark.asyncio
async def test_lever_pages_retains_specialists_and_excludes_talent_pools():
    calls = []

    def handler(request):
        skip = int(request.url.params["skip"])
        calls.append(skip)
        rows = [posting(), posting("2", title="Talent Pool")]
        return httpx.Response(200, json=rows if skip == 0 else [])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = LeverUKProvider(
            name="example", employer="Example", site="example", client=client
        )
        provider.page_size = 2
        jobs = await provider.search()
        assert calls == [0, 2]
        assert len(jobs) == 1
        assert jobs[0].title == "Software Engineer"
        assert "Engineering degree" in jobs[0].description
        assert jobs[0].workplace_type == "hybrid"
        assert jobs[0].posted_at is None
        assert provider.complete_snapshot


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,payload", [(403, {}), (429, {}), (200, {}), (200, [posting(), posting()])]
)
async def test_lever_failure_is_never_successful_zero(status, payload):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(status, json=payload))
    ) as client:
        provider = LeverUKProvider(
            name="example", employer="Example", site="example", client=client
        )
        with pytest.raises(ProviderError):
            await provider.search()
        assert not provider.complete_snapshot
        assert not provider.authoritative_empty


@pytest.mark.asyncio
async def test_lever_verified_empty_and_filtered_snapshot_are_distinct():
    rows = []
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=rows))
    ) as client:
        provider = LeverUKProvider(
            name="example", employer="Example", site="example", client=client
        )
        assert await provider.search() == []
        assert provider.complete_snapshot and provider.authoritative_empty
        rows.append(posting())
        assert await provider.search(keyword="no such role") == []
        assert not provider.complete_snapshot
        assert not provider.authoritative_empty


def domino_page(expiry="2099-12-31"):
    return (
        '<script type="application/ld+json">'
        + json.dumps(
            {
                "@type": "JobPosting",
                "title": "Finance Manager",
                "description": "<p>Qualified accountant required.</p>",
                "validThrough": expiry,
                "jobLocation": {
                    "address": {
                        "addressCountry": "GB",
                        "addressLocality": "Milton Keynes",
                    }
                },
            }
        )
        + "</script>"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "sitemap_host", ["jobs.dominos.co.uk", "dominosweb.eploy.net", "unrelated.example"]
)
@pytest.mark.parametrize(
    "count,robots,fails",
    [
        (1, "User-agent: *\nAllow: /", False),
        (2, "User-agent: *\nAllow: /", True),
        (1, "User-agent: *\nDisallow: /", True),
    ],
)
async def test_dominos_published_sitemap_and_permission_guards(
    count, robots, fails, sitemap_host
):
    url = DominosUKProvider.root + "/vacancies/722/finance.html"
    sitemap_posting = "https://" + sitemap_host + "/vacancies/722/finance.html"
    fails = fails or sitemap_host == "unrelated.example"

    def handler(request):
        assert request.url.host == "jobs.dominos.co.uk"
        path = request.url.path
        if path == "/robots.txt":
            text = robots
        elif path.endswith(".aspx"):
            text = f"<title>{count} Vacancies - Domino's</title>"
        elif path.endswith(".xml"):
            text = (
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                f"<url><loc>{sitemap_posting}</loc></url></urlset>"
            )
        else:
            text = domino_page()
        return httpx.Response(200, text=text)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = DominosUKProvider(client=client)
        if fails:
            with pytest.raises(ProviderError):
                await provider.search()
            assert not provider.complete_snapshot
        else:
            jobs = await provider.search()
            assert len(jobs) == 1
            assert jobs[0].external_id == "722"
            assert jobs[0].url == url
            assert jobs[0].workplace_type == "unknown"
            assert jobs[0].salary_min is None
            assert provider.complete_snapshot


@pytest.mark.asyncio
async def test_dominos_reconciles_removed_sitemap_posting_against_live_count():
    url = DominosUKProvider.root + "/vacancies/722/finance.html"

    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        if request.url.path.endswith(".aspx"):
            return httpx.Response(200, text="<title>1 Vacancies</title>")
        if request.url.path.endswith(".xml"):
            return httpx.Response(
                200,
                text=(
                    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                    f"<url><loc>{url}</loc></url>"
                    f"<url><loc>{DominosUKProvider.root}/vacancies/999/removed.html</loc></url>"
                    "</urlset>"
                ),
            )
        if request.url.path.endswith("removed.html"):
            return httpx.Response(410)
        return httpx.Response(200, text=domino_page())

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = DominosUKProvider(client=client)
        jobs = await provider.search()
        assert [job.external_id for job in jobs] == ["722"]
        assert provider.complete_snapshot


def test_dominos_expired_and_missing_structured_data():
    provider = DominosUKProvider()
    url = provider.root + "/vacancies/722/finance.html"
    assert provider._normalize(domino_page("2000-01-01"), url) is None
    current = provider._normalize(domino_page(), url)
    assert current.expires_at > datetime.now(UTC)
    with pytest.raises(ProviderError):
        provider._normalize("<html>Challenge or changed page</html>", url)
