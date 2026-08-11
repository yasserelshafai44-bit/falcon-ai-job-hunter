from app.integrations.registry import ConnectorRegistry
from app.integrations.remotive import RemotiveConnector


def build_default_registry() -> ConnectorRegistry:
    registry = ConnectorRegistry()
    registry.register(RemotiveConnector())
    return registry
