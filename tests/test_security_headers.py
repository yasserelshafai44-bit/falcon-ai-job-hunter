from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.production import configure_production_app


def test_security_headers_are_added() -> None:
    app = FastAPI()
    configure_production_app(app)

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"status": "ok"}

    response = TestClient(app).get("/ping")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "x-request-id" in response.headers
