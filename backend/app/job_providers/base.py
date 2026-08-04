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
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str | None = None
    posted_at: datetime | None = None


class JobProvider(ABC):
    name: str

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
