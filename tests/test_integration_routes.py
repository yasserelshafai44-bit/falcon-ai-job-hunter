from app.api.routes.integrations import router


def test_integration_router_exposes_expected_routes() -> None:
    paths = {route.path for route in router.routes}
    assert "/integrations/connectors" in paths
    assert "/integrations/connectors/{connector_name}/search" in paths
