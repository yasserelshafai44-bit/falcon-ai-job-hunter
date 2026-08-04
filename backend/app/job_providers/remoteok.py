from datetime import UTC, datetime
from html import unescape
import re
from typing import Any

import httpx

from app.job_providers.base import JobProvider, NormalizedJob


class RemoteOKProvider(JobProvider):
    name = "remoteok"
    endpoint = "https://remoteok.com/api"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

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
            timeout=20,
            follow_redirects=True,
            headers={"User-Agent": "FalconAIJobHunter/0.5"},
        )
        try:
            response = await client.get(self.endpoint)
            response.raise_for_status()
            payload = response.json()
        finally:
            if owns_client:
                await client.aclose()

        if not isinstance(payload, list):
            raise ValueError("Unexpected Remote OK payload")

        wanted = keyword.casefold().strip() if keyword else None
        jobs: list[NormalizedJob] = []

        for item in payload:
            if not isinstance(item, dict) or "id" not in item:
                continue

            title = str(item.get("position") or "").strip()
            company = str(item.get("company") or "").strip()
            description = _strip_html(str(item.get("description") or ""))
            tags = " ".join(str(tag) for tag in item.get("tags") or [])
            searchable = f"{title} {company} {description} {tags}".casefold()

            if wanted and wanted not in searchable:
                continue

            jobs.append(
                NormalizedJob(
                    provider=self.name,
                    external_id=str(item["id"]),
                    title=title or "Untitled role",
                    company=company or "Unknown company",
                    location=str(item.get("location") or "Remote"),
                    description=description,
                    url=str(item.get("url") or item.get("apply_url") or ""),
                    remote=True,
                    salary_min=_to_int(item.get("salary_min")),
                    salary_max=_to_int(item.get("salary_max")),
                    currency="USD",
                    posted_at=_parse_datetime(item.get("date") or item.get("epoch")),
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
