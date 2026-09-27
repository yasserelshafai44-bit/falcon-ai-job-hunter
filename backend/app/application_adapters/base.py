from typing import Protocol


class ApplicationAdapter(Protocol):
    name: str

    async def inspect(self, url: str) -> dict: ...

    def populate(self, profile: dict, configuration: dict) -> dict: ...


class BrowserApplicationAdapter(Protocol):
    """Visible local UI adapter; it cannot submit during a dry run."""

    name: str

    async def open(self, url: str) -> None: ...

    async def populate(self, profile: dict, resume_path, cover_text: str) -> None: ...

    async def observe(self, profile: dict) -> dict: ...
