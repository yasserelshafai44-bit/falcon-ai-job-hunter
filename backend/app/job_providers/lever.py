"""Read-only client for Lever's documented, public published-postings API."""

import re
from datetime import UTC, datetime
from urllib.parse import urlsplit

import httpx

from app.job_providers.base import JobProvider, NormalizedJob, ProviderError
from app.job_providers.location import normalize_location
from app.job_providers.smartrecruiters import _html_to_text


class LeverUKProvider(JobProvider):
    page_size = 100
    max_pages = 100

    def __init__(self, *, name, employer, site, client=None):
        self.name = name
        self.employer = employer
        self.display_name = f"{employer} UK Careers"
        self.site = site
        self._client = client

    async def search(self, *, keyword=None, location=None, limit=10000):
        self.complete_snapshot = False
        self.authoritative_empty = False
        client = self._client or httpx.AsyncClient(timeout=30)
        seen = set()
        jobs = []
        try:
            for page in range(self.max_pages):
                response = await client.get(
                    f"https://api.lever.co/v0/postings/{self.site}",
                    params={
                        "mode": "json",
                        "skip": page * self.page_size,
                        "limit": self.page_size,
                    },
                )
                response.raise_for_status()
                batch = response.json()
                if not isinstance(batch, list):
                    raise ProviderError(f"{self.display_name}: invalid posting list")
                for item in batch:
                    identifier = item.get("id") if isinstance(item, dict) else None
                    if not identifier or identifier in seen:
                        raise ProviderError(
                            f"{self.display_name}: missing/repeated posting ID"
                        )
                    seen.add(identifier)
                    job = self._normalize(item)
                    if job is not None:
                        jobs.append(job)
                if len(batch) < self.page_size:
                    break
            else:
                raise ProviderError(f"{self.display_name}: incomplete pagination")
        except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
            raise ProviderError(
                f"{self.display_name}: public feed request/validation failed"
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

    def _normalize(self, item):
        category = item.get("categories") or {}
        title = str(item.get("text") or "").strip()
        # Expressions of interest are not current vacancies.
        if re.search(
            r"talent (?:pool|community)|general opportunit|future opportunit",
            title,
            re.I,
        ):
            return None
        places = category.get("allLocations") or [category.get("location", "")]
        country = str(item.get("country") or "").upper()
        uk = [
            p
            for p in places
            if normalize_location(str(p)).is_uk is True
            and not (country and country != "GB" and p == category.get("location"))
        ]
        if country == "GB":
            uk = uk or [category.get("location") or "United Kingdom"]
        if not uk:
            return None
        url = item.get("hostedUrl") or ""
        if urlsplit(url).hostname != "jobs.lever.co" or not urlsplit(
            url
        ).path.startswith(f"/{self.site}/"):
            raise ProviderError(f"{self.display_name}: invalid official posting URL")
        description = "\n\n".join(
            filter(
                None,
                [
                    item.get("descriptionPlain")
                    or _html_to_text(item.get("description")),
                    *[
                        str(section.get("text") or "")
                        + "\n"
                        + _html_to_text(section.get("content"))
                        for section in item.get("lists", [])
                    ],
                    item.get("additionalPlain")
                    or _html_to_text(item.get("additional")),
                ],
            )
        )
        if not title or not description:
            raise ProviderError(f"{self.display_name}: incomplete posting")
        workplace = item.get("workplaceType", "unknown")
        if workplace not in {"remote", "hybrid", "on-site"}:
            workplace = "unknown"
        return NormalizedJob(
            provider=self.name,
            external_id=str(item["id"]),
            title=title,
            company=self.employer,
            location=" / ".join(uk) + ", United Kingdom",
            description=description,
            url=url,
            remote=workplace == "remote",
            workplace_type=workplace,
            employment_type=category.get("commitment"),
            retrieved_at=datetime.now(UTC),
        )
