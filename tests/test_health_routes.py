from app.api.routes.system import router


def test_system_router_exposes_health_and_readiness() -> None:
    paths = {route.path for route in router.routes}

    assert "/health" in paths
    assert "/ready" in paths
