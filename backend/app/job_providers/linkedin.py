from app.job_providers.base import JobProvider, NormalizedJob


class LinkedInProvider(JobProvider):
    """Placeholder until an approved integration is configured."""

    name = "linkedin"

    async def search(
        self,
        *,
        keyword: str | None = None,
        location: str | None = None,
        limit: int = 50,
    ) -> list[NormalizedJob]:
        del keyword, location, limit
        return []

    async def health_check(self) -> bool:
        return False
