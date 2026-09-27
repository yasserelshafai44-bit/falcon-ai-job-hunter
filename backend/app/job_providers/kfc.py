import re
from datetime import UTC, datetime, timedelta
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
from app.job_providers.role_filter import classify_role


class KFCUKProvider(JobProvider):
    name = "kfc_uk"
    display_name = "KFC UK Careers"
    endpoint = "https://careers.kfc.co.uk/api/jobs"
    complete_snapshot = False
    max_payload_jobs = 2_000

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        *,
        endpoint: str | None = None,
        timeout_seconds: float = 30,
    ) -> None:
        self._client = client
        self.endpoint = endpoint or self.endpoint
        self.timeout_seconds = timeout_seconds

    async def search(
        self,
        *,
        keyword: str | None = None,
        location: str | None = None,
        limit: int = 200,
    ) -> list[NormalizedJob]:
        self.complete_snapshot = False
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_seconds, connect=10),
            follow_redirects=True,
            headers={
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": "FalconAIJobHunter/0.7",
            },
        )
        try:
            response = await client.get(self.endpoint)
            if response.status_code == 429:
                raise ProviderRateLimitError(
                    "KFC UK Careers rate limit reached; wait and try again"
                )
            try:
                response.raise_for_status()
                payload = response.json()
            except httpx.HTTPStatusError as exc:
                raise ProviderError(
                    "KFC UK Careers request failed with HTTP "
                    f"{exc.response.status_code}"
                ) from exc
            except ValueError as exc:
                raise ProviderError("KFC UK Careers returned malformed JSON") from exc
        except httpx.TimeoutException as exc:
            raise ProviderError("KFC UK Careers request timed out") from exc
        except httpx.RequestError as exc:
            raise ProviderError("KFC UK Careers could not be reached") from exc
        finally:
            if owns_client:
                await client.aclose()

        items = payload.get("jobs") if isinstance(payload, dict) else None
        if not isinstance(items, list) or len(items) > self.max_payload_jobs:
            raise ProviderError("KFC UK Careers returned an unexpected response shape")
        total = _to_int(payload.get("results_total"))
        self.complete_snapshot = total is not None and total == len(items)
        retrieved_at = datetime.now(UTC)
        wanted = keyword.casefold().strip() if keyword else None
        wanted_location = location.casefold().strip() if location else None
        jobs: list[NormalizedJob] = []
        seen_external_ids: set[str] = set()
        for item in items:
            job = _normalize_job(item, retrieved_at)
            if job is None or not classify_role(job.title, job.description).eligible:
                continue
            if job.external_id in seen_external_ids:
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
            seen_external_ids.add(job.external_id)
            if len(jobs) >= max(1, min(limit, 500)):
                self.complete_snapshot = False
                break
        return jobs


def _normalize_job(item: Any, retrieved_at: datetime) -> NormalizedJob | None:
    if not isinstance(item, dict):
        return None
    title = str(item.get("job_title") or "").strip()
    description = _strip_html(str(item.get("description_html") or ""))
    url = str(item.get("job_url") or "").strip()
    external_id = str(item.get("ats_id") or item.get("id") or "").strip()
    country = str(item.get("location_country") or "").strip()
    city = str(item.get("location_city") or "").strip()
    postcode = str(item.get("location_postcode") or "").strip()
    if postcode.upper().startswith("BT"):
        country = "Northern Ireland"
    location = ", ".join(part for part in (city, country, postcode) if part)
    if (
        not title
        or not description
        or not external_id
        or not url.startswith("https://careers.kfc.co.uk/jobs/")
    ):
        return None
    telecommuting = bool(item.get("location_telecommuting"))
    workplace = str(item.get("workplace_reqs") or "").casefold()
    remote = telecommuting or "remote" in workplace
    salary_min, salary_max = _salary(str(item.get("salary_display") or ""))
    return NormalizedJob(
        provider="kfc_uk",
        external_id=external_id,
        title=title,
        company="KFC UK",
        location=location or "Location not specified",
        description=description,
        url=url,
        remote=remote,
        workplace_type="remote"
        if remote
        else ("hybrid" if "hybrid" in workplace else "on-site"),
        employment_type=str(item.get("employment_type") or "").strip() or None,
        salary_min=salary_min,
        salary_max=salary_max,
        currency="GBP" if salary_min or salary_max else None,
        posted_at=_parse_datetime(item.get("ats_created_timestamp_utc")),
        expires_at=_parse_closing_datetime(item.get("closing_date")),
        retrieved_at=retrieved_at,
    )


def _strip_html(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(value))).strip()


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        return None


def _parse_closing_datetime(value: Any) -> datetime | None:
    parsed = _parse_datetime(value)
    if parsed and parsed.hour == parsed.minute == parsed.second == 0:
        return parsed + timedelta(days=1)
    return parsed


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _salary(value: str) -> tuple[int | None, int | None]:
    numbers = [
        float(number) * (1_000 if suffix.casefold() == "k" else 1)
        for number, suffix in re.findall(r"£\s*([\d.]+)\s*([kK]?)", value)
    ]
    if not numbers:
        return None, None
    return round(numbers[0]), round(numbers[-1])
