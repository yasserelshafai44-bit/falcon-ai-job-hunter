import pytest

from app.integrations.base import JobSourceConnector, NormalizedJob
from app.integrations.registry import ConnectorRegistry


class FakeConnector(JobSourceConnector):
    name = "fake"

    async def search(
        self,
        *,
        query: str,
        location: str | None = None,
        limit: int = 25,
    ) -> list[NormalizedJob]:
        return []


def test_registry_registers_and_resolves_connectors() -> None:
    registry = ConnectorRegistry()
    connector = FakeConnector()
    registry.register(connector)
    assert registry.names() == ["fake"]
    assert registry.get("fake") is connector


def test_registry_rejects_unknown_connector() -> None:
    registry = ConnectorRegistry()
    with pytest.raises(KeyError):
        registry.get("missing")
