from app.integrations.base import JobSourceConnector


class ConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: dict[str, JobSourceConnector] = {}

    def register(self, connector: JobSourceConnector) -> None:
        if not connector.name:
            raise ValueError("Connector name is required")
        self._connectors[connector.name] = connector

    def get(self, name: str) -> JobSourceConnector:
        try:
            return self._connectors[name]
        except KeyError as exc:
            raise KeyError(f"Unknown connector: {name}") from exc

    def names(self) -> list[str]:
        return sorted(self._connectors)
