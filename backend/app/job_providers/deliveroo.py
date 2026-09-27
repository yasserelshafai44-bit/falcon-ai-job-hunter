import re
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


class DeliverooProvider(JobProvider):
    name = "deliveroo"
    display_name = "Deliveroo Careers"
    endpoint = "https://careers.deliveroo.co.uk/wp-json/wp/v2/roles"
    max_pages = 10
    page_size = 100
    complete_snapshot = False

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        *,
        endpoint: str | None = None,
        timeout_seconds: float = 20,
    ) -> None:
        self._client = client
        self.endpoint = endpoint or self.endpoint
        self.timeout_seconds = timeout_seconds

    async def search(
        self,
        *,
        keyword: str | None = None,
        location: str | None = None,
        limit: int = 50,
    ) -> list[NormalizedJob]:
        self.complete_snapshot = False
        self.authoritative_empty = False
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_seconds, connect=10),
            follow_redirects=True,
            headers={"User-Agent": "FalconAIJobHunter/0.6"},
        )
        jobs: list[NormalizedJob] = []
        page = 1
        total_pages: int | None = None
        seen_page_ids: set[tuple[str, ...]] = set()
        seen_external_ids: set[str] = set()
        retrieved_at = datetime.now(UTC)
        wanted = keyword.casefold().strip() if keyword else None
        wanted_location = location.casefold().strip() if location else None
        try:
            while page <= self.max_pages:
                response = await client.get(
                    self.endpoint, params={"per_page": self.page_size, "page": page}
                )
                if response.status_code == 429:
                    raise ProviderRateLimitError(
                        "Deliveroo Careers rate limit reached; wait and try again"
                    )
                try:
                    response.raise_for_status()
                    payload = response.json()
                except httpx.HTTPStatusError as exc:
                    raise ProviderError(
                        "Deliveroo Careers request failed with HTTP "
                        f"{exc.response.status_code}"
                    ) from exc
                except ValueError as exc:
                    raise ProviderError(
                        "Deliveroo Careers returned malformed JSON"
                    ) from exc
                if not isinstance(payload, list):
                    raise ProviderError(
                        "Deliveroo Careers returned an unexpected response shape"
                    )
                header_pages = _positive_int(response.headers.get("X-WP-TotalPages"))
                total_pages = header_pages or total_pages
                page_ids = tuple(
                    str(item.get("id"))
                    for item in payload
                    if isinstance(item, dict) and item.get("id") is not None
                )
                if page_ids in seen_page_ids:
                    raise ProviderError(
                        "Deliveroo Careers pagination repeated a page unexpectedly"
                    )
                seen_page_ids.add(page_ids)
                for item in payload:
                    job = _normalize_job(item, retrieved_at)
                    if job is None:
                        continue
                    if job.external_id in seen_external_ids:
                        continue
                    normalized = normalize_location(
                        job.location,
                        remote=job.remote,
                        workplace_type=job.workplace_type,
                    )
                    if normalized.is_uk is not True:
                        continue
                    searchable = f"{job.title} {job.description}".casefold()
                    if wanted and wanted not in searchable:
                        continue
                    if (
                        wanted_location
                        and wanted_location not in job.location.casefold()
                    ):
                        continue
                    jobs.append(job)
                    seen_external_ids.add(job.external_id)
                    if len(jobs) >= max(1, min(limit, 10000)):
                        return jobs
                if (
                    not payload
                    or len(payload) < self.page_size
                    or (total_pages is not None and page >= total_pages)
                ):
                    self.complete_snapshot = keyword is None and location is None
                    break
                page += 1
            else:
                raise ProviderError(
                    "Deliveroo Careers exceeded the safe pagination limit"
                )
        except httpx.TimeoutException as exc:
            raise ProviderError("Deliveroo Careers request timed out") from exc
        except httpx.RequestError as exc:
            raise ProviderError("Deliveroo Careers could not be reached") from exc
        finally:
            if owns_client:
                await client.aclose()
        self.authoritative_empty = self.complete_snapshot and not jobs
        return jobs


def _normalize_job(item: Any, retrieved_at: datetime) -> NormalizedJob | None:
    if (
        not isinstance(item, dict)
        or item.get("status") != "publish"
        or item.get("id") is None
    ):
        return None
    meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
    title = _rendered(item, "title")
    description = _strip_html(_rendered(item, "content"))
    location = str(
        meta.get("ats_location")
        or meta.get("ashby_location")
        or meta.get("greenhouse_location")
        or "Location not specified"
    ).strip()
    url = str(item.get("link") or "").strip()
    if (
        not title
        or not description
        or not url.startswith("https://careers.deliveroo.co.uk/role/")
    ):
        return None
    remote = bool(
        meta.get("ats_remote")
        or meta.get("ashby_remote")
        or meta.get("greenhouse_remote")
    )
    workplace = (
        "remote"
        if remote
        else ("hybrid" if "hybrid" in location.casefold() else "on-site")
    )
    return NormalizedJob(
        provider="deliveroo",
        external_id=str(meta.get("ashby_req_id") or item["id"]),
        title=title,
        company="Deliveroo",
        location=location,
        description=description,
        url=url,
        remote=remote,
        workplace_type=workplace,
        posted_at=_parse_datetime(item.get("date_gmt") or item.get("date")),
        retrieved_at=retrieved_at,
    )


def _rendered(item: dict[str, Any], field: str) -> str:
    value = item.get(field)
    return (
        unescape(str(value.get("rendered") or "")).strip()
        if isinstance(value, dict)
        else ""
    )


def _strip_html(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        return None


def _positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None
