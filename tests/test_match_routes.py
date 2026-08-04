from app.api.routes.matches import router


def test_match_router_exposes_expected_routes() -> None:
    paths = {route.path for route in router.routes}

    assert "/matches/jobs/{job_id}/score" in paths
    assert "/matches" in paths
    assert "/matches/{match_id}" in paths
    assert "/matches/recalculate" in paths
