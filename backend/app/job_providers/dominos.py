"""Official Domino's corporate board and employer-published JobPosting JSON-LD.

Not a franchise-wide feed. A count mismatch fails closed: never reconcile a
partial listing or follow a browser challenge/login flow.
"""

import asyncio
import json
import re
from datetime import UTC, datetime, time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from xml.etree import ElementTree

import httpx

from app.job_providers.base import JobProvider, NormalizedJob, ProviderError
from app.job_providers.smartrecruiters import _html_to_text


class DominosUKProvider(JobProvider):
    name = "dominos_uk"
    display_name = "Domino's UK Corporate Careers"
    root = "https://jobs.dominos.co.uk"
    listing = root + "/vacancies/vacancy-search-results.aspx"

    def __init__(self, client=None):
        self._client = client

    async def search(self, *, keyword=None, location=None, limit=10000):
        self.complete_snapshot = False
        self.authoritative_empty = False
        client = self._client or httpx.AsyncClient(timeout=30, follow_redirects=True)
        try:
            response = await client.get(self.root + "/robots.txt")
            response.raise_for_status()
            robots = RobotFileParser()
            robots.parse(response.text.splitlines())
            if not robots.can_fetch("FalconAIJobHunter", self.listing):
                raise ProviderError(
                    "Domino's does not permit automatic listing retrieval"
                )
            response = await client.get(self.listing)
            response.raise_for_status()
            count = re.search(r"<title>\s*(\d+) Vacancies", response.text, re.I)
            sitemap_url = self.root + "/live-jobs.xml"
            if not robots.can_fetch("FalconAIJobHunter", sitemap_url):
                raise ProviderError(
                    "Domino's does not permit automatic sitemap retrieval"
                )
            sitemap = await client.get(sitemap_url)
            sitemap.raise_for_status()
            links = sorted(
                set(
                    node.text
                    for node in ElementTree.fromstring(sitemap.content).iter(
                        "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
                    )
                    if node.text
                )
            )
            unexpected = next(
                (
                    u
                    for u in links
                    if (
                        urlsplit(u).hostname
                        not in {"jobs.dominos.co.uk", "dominosweb.eploy.net"}
                        or not re.match(r"/vacancies/\d+/", urlsplit(u).path)
                    )
                ),
                None,
            )
            if unexpected:
                raise ProviderError(
                    "Domino's sitemap contains an unexpected vacancy URL: "
                    f"host={urlsplit(unexpected).hostname!r}, "
                    f"path={urlsplit(unexpected).path[:160]!r}"
                )
            # Eploy sometimes emits its tenant hostname in the official sitemap.
            # That tenant's robots.txt points back to jobs.dominos.co.uk/sitemap.xml.
            # Use the public employer URL for the same posting, never arbitrary hosts.
            links = sorted({self.root + urlsplit(u).path for u in links})
            jobs = []
            # Low request rate, with any declared crawl delay honoured.
            delay = max(0.2, robots.crawl_delay("FalconAIJobHunter") or 0)
            for url in links:
                if not robots.can_fetch("FalconAIJobHunter", url):
                    raise ProviderError(
                        "Domino's posting disallows automated retrieval"
                    )
                await asyncio.sleep(delay)
                response = await client.get(url)
                if response.status_code in {404, 410}:
                    continue
                response.raise_for_status()
                job = self._normalize(response.text, url)
                if job is not None:
                    jobs.append(job)
            if not count or int(count[1]) != len(jobs):
                raise ProviderError(
                    "Domino's listing count changed or pagination is incomplete"
                )
        except (
            httpx.HTTPError,
            ValueError,
            TypeError,
            KeyError,
            ElementTree.ParseError,
        ) as exc:
            raise ProviderError(
                "Domino's public board retrieval/validation failed"
            ) from exc
        finally:
            if self._client is None:
                await client.aclose()
        selected = [
            j
            for j in jobs
            if (
                not keyword
                or keyword.casefold() in (j.title + " " + j.description).casefold()
            )
            and (not location or location.casefold() in j.location.casefold())
        ]
        self.complete_snapshot = not keyword and not location and len(selected) <= limit
        self.authoritative_empty = self.complete_snapshot and not selected
        return selected[:limit]

    def _normalize(self, html, url):
        objects = []
        for raw in re.findall(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html,
            re.S | re.I,
        ):
            data = json.loads(raw)
            objects.extend(
                data if isinstance(data, list) else data.get("@graph", [data])
            )
        data = next((d for d in objects if d.get("@type") == "JobPosting"), None)
        if not data:
            raise ProviderError("Domino's posting has no JobPosting structured data")
        expiry = None
        if data.get("validThrough"):
            value = data["validThrough"]
            expiry = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if len(value) == 10:
                expiry = datetime.combine(expiry.date(), time.max)
            expiry = expiry.replace(tzinfo=UTC) if expiry.tzinfo is None else expiry
            if expiry <= datetime.now(UTC):
                return None
        address = data.get("jobLocation", {}).get("address", {})
        if str(address.get("addressCountry", "")).casefold() not in {
            "gb",
            "uk",
            "united kingdom",
        }:
            return None
        title = str(data.get("title") or "").strip()
        description = _html_to_text(data.get("description"))
        if (
            not title
            or not description
            or urlsplit(url).hostname != "jobs.dominos.co.uk"
        ):
            raise ProviderError("Domino's posting is incomplete")
        place = ", ".join(
            str(address[k])
            for k in [
                "addressLocality",
                "addressRegion",
                "postalCode",
                "addressCountry",
            ]
            if address.get(k)
        )
        return NormalizedJob(
            provider=self.name,
            external_id=urlsplit(url).path.split("/")[2],
            title=title,
            company="Domino's UK & Ireland",
            location=place,
            description=description,
            url=url,
            remote=False,
            workplace_type="unknown",
            employment_type=data.get("employmentType"),
            expires_at=expiry,
            retrieved_at=datetime.now(UTC),
        )
