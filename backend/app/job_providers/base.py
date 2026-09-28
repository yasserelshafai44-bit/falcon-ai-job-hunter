from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class NormalizedJob:
    provider: str
    external_id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    remote: bool
    workplace_type: str = "unknown"
    requirements: tuple[str, ...] = ()
    employment_type: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str | None = None
    posted_at: datetime | None = None
    expires_at: datetime | None = None
    retrieved_at: datetime | None = None
    is_demo: bool = False


class ProviderError(RuntimeError):
    """Safe provider failure suitable for returning to an authenticated client."""


class ProviderRateLimitError(ProviderError):
    """The upstream provider rejected the request because of a rate limit."""


class JobProvider(ABC):
    name: str
    display_name: str
    is_demo: bool = False
    complete_snapshot: bool = False
    authoritative_empty: bool = False
    refresh_timeout_seconds: float = 600

    @abstractmethod
    async def search(
        self,
        *,
        keyword: str | None = None,
        location: str | None = None,
        limit: int = 50,
    ) -> list[NormalizedJob]:
        raise NotImplementedError

    async def health_check(self) -> bool:
        return True
