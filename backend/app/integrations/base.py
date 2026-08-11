from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class NormalizedJob:
    source: str
    external_id: str
    title: str
    company: str
    location: str | None
    description: str
    url: str
    remote: bool = False
    metadata: dict[str, Any] | None = None


class JobSourceConnector(ABC):
    name: str

    @abstractmethod
    async def search(
        self,
        *,
        query: str,
        location: str | None = None,
        limit: int = 25,
    ) -> list[NormalizedJob]:
        raise NotImplementedError
