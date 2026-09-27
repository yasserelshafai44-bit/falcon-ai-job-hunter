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


class RemoteOKProvider(JobProvider):
    name = "remoteok"
    display_name = "Remote OK"
    endpoint = "https://remoteok.com/api"

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
        del location
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(
            timeout=self.timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": "FalconAIJobHunter/0.5"},
        )
        try:
            response = await client.get(self.endpoint)
            if response.status_code == 429:
                raise ProviderRateLimitError(
                    "Remote OK rate limit reached; wait and try the refresh again"
                )
            try:
                response.raise_for_status()
                payload = response.json()
            except httpx.HTTPStatusError as exc:
                raise ProviderError(
                    f"Remote OK request failed with HTTP {exc.response.status_code}"
                ) from exc
            except ValueError as exc:
                raise ProviderError("Remote OK returned malformed JSON") from exc
        finally:
            if owns_client:
                await client.aclose()

        if not isinstance(payload, list):
            raise ProviderError("Remote OK returned an unexpected response shape")

        wanted = keyword.casefold().strip() if keyword else None
        jobs: list[NormalizedJob] = []

        for item in payload:
            if not isinstance(item, dict) or "id" not in item:
                continue

            title = str(item.get("position") or "").strip()
            company = str(item.get("company") or "").strip()
            description = _strip_html(str(item.get("description") or ""))
            url = str(item.get("url") or item.get("apply_url") or "").strip()
            if not title or not company or not description or not _valid_url(url):
                continue
            tags = " ".join(str(tag) for tag in item.get("tags") or [])
            searchable = f"{title} {company} {description} {tags}".casefold()

            if wanted and wanted not in searchable:
                continue

            jobs.append(
                NormalizedJob(
                    provider=self.name,
                    external_id=str(item["id"]),
                    title=title,
                    company=company,
                    location=str(
                        item.get("location") or "Location not specified"
                    ).strip(),
                    description=description,
                    url=url,
                    remote=True,
                    workplace_type="remote",
                    requirements=tuple(
                        str(tag).strip()
                        for tag in item.get("tags") or []
                        if str(tag).strip()
                    ),
                    employment_type=str(item.get("type") or "").strip() or None,
                    salary_min=_to_int(item.get("salary_min")),
                    salary_max=_to_int(item.get("salary_max")),
                    currency=(
                        str(item.get("currency") or "USD")
                        if _to_int(item.get("salary_min"))
                        or _to_int(item.get("salary_max"))
                        else None
                    ),
                    posted_at=_parse_datetime(item.get("date") or item.get("epoch")),
                    retrieved_at=datetime.now(UTC),
                )
            )
            if len(jobs) >= max(1, min(limit, 200)):
                break

        return jobs

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(
                timeout=10,
                follow_redirects=True,
                headers={"User-Agent": "FalconAIJobHunter/0.5"},
            ) as client:
                response = await client.get(self.endpoint)
                return response.status_code == 200
        except httpx.HTTPError:
            return False


def _strip_html(value: str) -> str:
    plain = re.sub(r"<[^>]+>", " ", unescape(value))
    return re.sub(r"\s+", " ", plain).strip()


def _valid_url(value: str) -> bool:
    return value.casefold().startswith(
        ("https://remoteok.com/", "https://remoteok.io/")
    )


def _to_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=UTC)
    if isinstance(value, str):
        try:
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return result if result.tzinfo else result.replace(tzinfo=UTC)
        except ValueError:
            return None
    return None
