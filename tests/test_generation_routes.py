from app.api.routes.generation import router

def test_generation_router_exposes_expected_routes() -> None:
    paths = {route.path for route in router.routes}
    assert "/resume/generate" in paths
    assert "/cover-letter/generate" in paths
    assert "/generation/history" in paths
