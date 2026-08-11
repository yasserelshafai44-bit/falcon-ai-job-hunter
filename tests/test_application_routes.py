from app.api.routes.applications import router


def test_application_workflow_router_exposes_expected_routes() -> None:
    paths = {route.path for route in router.routes}

    assert "/application-workflows" in paths
    assert "/application-workflows/{workflow_id}" in paths
    assert "/application-workflows/{workflow_id}/documents" in paths
    assert "/application-workflows/{workflow_id}/request-approval" in paths
    assert "/application-workflows/{workflow_id}/approve" in paths
    assert "/application-workflows/{workflow_id}/submitted" in paths
    assert "/application-workflows/{workflow_id}/outcome" in paths
