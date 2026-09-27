from app.api.routes.applications import router
from app.schemas.application_workflow import SubmissionRequest


def test_application_workflow_router_exposes_expected_routes() -> None:
    paths = {route.path for route in router.routes}

    assert "/application-workflows" in paths
    assert "/application-workflows/{workflow_id}" in paths
    assert "/application-workflows/{workflow_id}/review" in paths
    assert "/application-workflows/{workflow_id}/reviewed" in paths
    assert "/application-workflows/{workflow_id}/documents" in paths
    assert "/application-workflows/{workflow_id}/request-approval" in paths
    assert "/application-workflows/{workflow_id}/approve" in paths
    assert "/application-workflows/{workflow_id}/submitted" in paths
    assert "/application-workflows/{workflow_id}/outcome" in paths


def test_submission_requires_explicit_confirmation_schema() -> None:
    assert SubmissionRequest().confirmed_submitted is False
