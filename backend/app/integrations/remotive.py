from typing import Any

import httpx

from app.integrations.base import JobSourceConnector, NormalizedJob


class RemotiveConnector(JobSourceConnector):
    name = "remotive"
    endpoint = "https://remotive.com/api/remote-jobs"

    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        timeout: float = 20.0,
    ) -> None:
        self._client = client
        self._timeout = timeout

    async def search(
        self,
        *,
        query: str,
        location: str | None = None,
        limit: int = 25,
    ) -> list[NormalizedJob]:
        if limit < 1:
            raise ValueError("limit must be at least 1")

        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        try:
            response = await client.get(self.endpoint, params={"search": query})
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
        finally:
            if owns_client:
                await client.aclose()

        jobs: list[NormalizedJob] = []
        for raw in payload.get("jobs", []):
            candidate = self._normalize(raw)
            if location and candidate.location:
                if location.casefold() not in candidate.location.casefold():
                    continue
            jobs.append(candidate)
            if len(jobs) >= limit:
                break
        return jobs

    def _normalize(self, raw: dict[str, Any]) -> NormalizedJob:
        external_id = str(raw.get("id", ""))
        if not external_id:
            raise ValueError("Remotive job is missing id")

        return NormalizedJob(
            source=self.name,
            external_id=external_id,
            title=str(raw.get("title") or ""),
            company=str(raw.get("company_name") or ""),
            location=str(raw.get("candidate_required_location") or "") or None,
            description=str(raw.get("description") or ""),
            url=str(raw.get("url") or ""),
            remote=True,
            metadata={
                "category": raw.get("category"),
                "publication_date": raw.get("publication_date"),
                "salary": raw.get("salary"),
            },
        )
