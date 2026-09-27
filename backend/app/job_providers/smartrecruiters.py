import asyncio
import re
from dataclasses import replace
from datetime import UTC, datetime
from html import unescape
from typing import Any

import httpx

from app.job_providers.base import (
    JobProvider,
    NormalizedJob,
    ProviderError,
    ProviderRateLimitError,
)
from app.job_providers.location import normalize_location


class SmartRecruitersProvider(JobProvider):
    """Reusable adapter for an employer's public SmartRecruiters postings feed."""

    api_root = "https://api.smartrecruiters.com/v1/companies"
    page_size = 100
    max_pages = 100
    max_detail_concurrency = 5
    complete_snapshot = False

    def __init__(
        self,
        *,
        name: str,
        display_name: str,
        company_identifier: str,
        employer: str,
        country_code: str = "gb",
        search_queries: tuple[str, ...] = (),
        client: httpx.AsyncClient | None = None,
        api_root: str | None = None,
        timeout_seconds: float = 20,
    ) -> None:
        self.name = name
        self.display_name = display_name
        self.company_identifier = company_identifier
        self.employer = employer
        self.country_code = country_code.casefold()
        self.search_queries = search_queries
        self._client = client
        self.api_root = (api_root or self.api_root).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.cached_jobs: dict[str, NormalizedJob] = {}

    @property
    def postings_endpoint(self) -> str:
        return f"{self.api_root}/{self.company_identifier}/postings"

    async def search(
        self,
        *,
        keyword: str | None = None,
        location: str | None = None,
        limit: int = 200,
    ) -> list[NormalizedJob]:
        self.complete_snapshot = False
        self.authoritative_empty = False
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_seconds, connect=10),
            follow_redirects=True,
            headers={
                "Accept": "application/json",
                "User-Agent": "FalconAIJobHunter/0.8",
            },
        )
        try:
            summaries = await self._fetch_all_summaries(client)
            semaphore = asyncio.Semaphore(self.max_detail_concurrency)

            async def fetch(item: dict[str, Any]) -> dict[str, Any] | NormalizedJob:
                cached = self.cached_jobs.get(str(item["id"]))
                released = _parse_datetime(item.get("releasedDate"))
                # Posting API content changes require republishing. Always read
                # the complete current list; reuse detail only for the same release.
                if (
                    cached
                    and released
                    and cached.posted_at
                    and cached.posted_at.replace(tzinfo=UTC) == released
                    and cached.title == item.get("name")
                ):
                    return replace(cached, retrieved_at=datetime.now(UTC))
                async with semaphore:
                    return await self._fetch_detail(client, str(item["id"]))

            details = await asyncio.gather(*(fetch(item) for item in summaries))
        except httpx.TimeoutException as exc:
            raise ProviderError(f"{self.display_name} request timed out") from exc
        except httpx.RequestError as exc:
            raise ProviderError(f"{self.display_name} could not be reached") from exc
        finally:
            if owns_client:
                await client.aclose()

        retrieved_at = datetime.now(UTC)
        wanted = keyword.casefold().strip() if keyword else None
        wanted_location = location.casefold().strip() if location else None
        jobs: list[NormalizedJob] = []
        seen: set[str] = set()
        for detail in details:
            job = (
                detail
                if isinstance(detail, NormalizedJob)
                else self._normalize(detail, retrieved_at)
            )
            if job is None or job.external_id in seen:
                continue
            normalized = normalize_location(
                job.location, remote=job.remote, workplace_type=job.workplace_type
            )
            if normalized.is_uk is not True:
                continue
            if wanted and wanted not in f"{job.title} {job.description}".casefold():
                continue
            if wanted_location and wanted_location not in job.location.casefold():
                continue
            jobs.append(job)
            seen.add(job.external_id)

        safe_limit = max(1, min(limit, 10000))
        self.complete_snapshot = (
            keyword is None and location is None and len(jobs) <= safe_limit
        )
        if len(jobs) > safe_limit:
            self.complete_snapshot = False
        self.authoritative_empty = self.complete_snapshot and not jobs
        return jobs[:safe_limit]

    async def _fetch_all_summaries(
        self, client: httpx.AsyncClient
    ) -> list[dict[str, Any]]:
        if not self.search_queries:
            return await self._fetch_query_summaries(client, query=None)
        summaries: list[dict[str, Any]] = []
        seen: set[str] = set()
        for query in self.search_queries:
            for item in await self._fetch_query_summaries(client, query=query):
                external_id = str(item["id"])
                if external_id not in seen:
                    summaries.append(item)
                    seen.add(external_id)
        return summaries

    async def _fetch_query_summaries(
        self,
        client: httpx.AsyncClient,
        *,
        query: str | None,
    ) -> list[dict[str, Any]]:
        summaries: list[dict[str, Any]] = []
        seen_pages: set[tuple[str, ...]] = set()
        offset = 0
        total: int | None = None
        for _ in range(self.max_pages):
            params: dict[str, str | int] = {
                "limit": self.page_size,
                "offset": offset,
                "country": self.country_code,
                "destination": "PUBLIC",
            }
            if query:
                params["q"] = query
            response = await client.get(self.postings_endpoint, params=params)
            payload = self._json_response(response)
            content = payload.get("content") if isinstance(payload, dict) else None
            if not isinstance(content, list) or any(
                not isinstance(item, dict) or not item.get("id") for item in content
            ):
                raise ProviderError(
                    f"{self.display_name} returned an unexpected response shape"
                )
            reported_total = _non_negative_int(payload.get("totalFound"))
            if reported_total is None:
                raise ProviderError(
                    f"{self.display_name} did not report a valid vacancy total"
                )
            total = reported_total if total is None else total
            if reported_total != total:
                raise ProviderError(
                    f"{self.display_name} vacancy total changed during pagination"
                )
            ids = tuple(str(item["id"]) for item in content)
            if ids and ids in seen_pages:
                raise ProviderError(
                    f"{self.display_name} pagination repeated a page unexpectedly"
                )
            seen_pages.add(ids)
            previous_ids = {str(item["id"]) for item in summaries}
            if previous_ids.intersection(ids):
                raise ProviderError(
                    f"{self.display_name} pagination returned duplicate vacancies"
                )
            summaries.extend(content)
            if len(summaries) >= total:
                return summaries
            if not content:
                raise ProviderError(
                    f"{self.display_name} pagination ended before the reported total"
                )
            offset += len(content)
        raise ProviderError(f"{self.display_name} exceeded the safe pagination limit")

    async def _fetch_detail(
        self, client: httpx.AsyncClient, external_id: str
    ) -> dict[str, Any]:
        payload = self._json_response(
            await client.get(f"{self.postings_endpoint}/{external_id}")
        )
        if not isinstance(payload, dict) or str(payload.get("id") or "") != external_id:
            raise ProviderError(
                f"{self.display_name} returned malformed vacancy detail"
            )
        return payload

    def _json_response(self, response: httpx.Response) -> Any:
        if response.status_code == 429:
            raise ProviderRateLimitError(
                f"{self.display_name} rate limit reached; wait and try again"
            )
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"{self.display_name} request failed with HTTP "
                f"{exc.response.status_code}"
            ) from exc
        except ValueError as exc:
            raise ProviderError(f"{self.display_name} returned malformed JSON") from exc

    def _normalize(
        self, detail: dict[str, Any], retrieved_at: datetime
    ) -> NormalizedJob | None:
        external_id = str(detail.get("id") or "").strip()
        title = str(detail.get("name") or "").strip()
        url = str(detail.get("postingUrl") or "").strip()
        location_data = detail.get("location")
        location_data = location_data if isinstance(location_data, dict) else {}
        country = str(location_data.get("country") or "").casefold()
        if not country:
            raise ProviderError(
                f"{self.display_name} vacancy detail omitted its country"
            )
        if country not in {self.country_code, "uk", "gb", "gbr"}:
            return None
        job_ad = detail.get("jobAd")
        job_ad = job_ad if isinstance(job_ad, dict) else {}
        sections_data = job_ad.get("sections")
        sections_data = sections_data if isinstance(sections_data, dict) else job_ad
        sections = [
            sections_data.get(key)
            for key in (
                "companyDescription",
                "jobDescription",
                "qualifications",
                "additionalInformation",
            )
        ]
        description = "\n\n".join(text for text in map(_section_text, sections) if text)
        if (
            not external_id
            or not title
            or not description
            or not _valid_posting_url(url)
        ):
            raise ProviderError(
                f"{self.display_name} returned incomplete vacancy detail"
            )
        location = _location_text(location_data)
        workplace = _workplace_type(detail, location_data, description)
        type_data = detail.get("typeOfEmployment")
        employment = (
            str(type_data.get("label") or "").strip()
            if isinstance(type_data, dict)
            else None
        )
        salary_min, salary_max, currency = _salary(detail)
        return NormalizedJob(
            provider=self.name,
            external_id=external_id,
            title=title,
            company=self.employer,
            location=location,
            description=description,
            url=url,
            remote=workplace == "remote",
            workplace_type=workplace,
            requirements=_list_items(
                _section_html(sections_data.get("qualifications"))
            ),
            employment_type=employment or None,
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            posted_at=_parse_datetime(detail.get("releasedDate")),
            retrieved_at=retrieved_at,
        )


def _valid_posting_url(url: str) -> bool:
    return url.startswith("https://jobs.smartrecruiters.com/")


def _html_to_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = re.sub(r"(?i)<\s*br\s*/?\s*>", "\n", value)
    value = re.sub(r"(?i)</\s*(?:p|li|div|h[1-6])\s*>", "\n", value)
    value = re.sub(r"<[^>]+>", "", unescape(value))
    return re.sub(r"\n\s*\n+", "\n", re.sub(r"[ \t]+", " ", value)).strip()


def _section_html(value: Any) -> Any:
    return value.get("text") if isinstance(value, dict) else value


def _section_text(value: Any) -> str:
    return _html_to_text(_section_html(value))


def _list_items(value: Any) -> tuple[str, ...]:
    if not isinstance(value, str):
        return ()
    return tuple(
        filter(
            None,
            (
                _html_to_text(item)
                for item in re.findall(r"(?is)<li[^>]*>(.*?)</li>", value)
            ),
        )
    )[:20]


def _location_text(location: dict[str, Any]) -> str:
    full = str(location.get("fullLocation") or "").strip(" ,")
    if full:
        return re.sub(r"\s*,\s*,+", ",", full)
    parts = [
        str(location.get(key) or "").strip() for key in ("city", "region", "postalCode")
    ]
    country = str(location.get("country") or "").strip()
    if country.casefold() in {"gb", "uk", "gbr"}:
        country = "United Kingdom"
    return ", ".join(filter(None, (*parts, country))) or "Location not specified"


def _workplace_type(
    detail: dict[str, Any], location: dict[str, Any], description: str
) -> str:
    if location.get("hybrid") is True:
        return "hybrid"
    if location.get("remote") is True:
        return "remote"
    text = " ".join(
        str(value or "")
        for value in (
            detail.get("workplaceType"),
            location.get("remote"),
            location.get("fullLocation"),
        )
    ).casefold()
    if "hybrid" in text:
        return "hybrid"
    if "remote" in text and "not remote" not in text:
        return "remote"
    if re.search(r"\bhybrid\b", description, re.IGNORECASE):
        return "hybrid"
    return "on-site"


def _salary(detail: dict[str, Any]) -> tuple[int | None, int | None, str | None]:
    custom = detail.get("customField")
    if isinstance(custom, list):
        text = " ".join(
            str(item.get("valueLabel") or "")
            for item in custom
            if isinstance(item, dict)
            and any(
                marker in str(item.get("fieldLabel") or "").casefold()
                for marker in ("salary", "compensation", "pay")
            )
        )
    elif isinstance(custom, dict):
        text = " ".join(
            str(value)
            for key, value in custom.items()
            if "salary" in str(key).casefold() or "compensation" in str(key).casefold()
        )
    else:
        text = ""
    numbers = [
        float(value.replace(",", "")) for value in re.findall(r"£\s*([\d,.]+)", text)
    ]
    return (
        (round(numbers[0]), round(numbers[-1]), "GBP")
        if numbers
        else (None, None, None)
    )


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        return None


def _non_negative_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None
