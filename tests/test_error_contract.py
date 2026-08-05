from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.production import configure_production_app


def test_http_errors_follow_consistent_contract() -> None:
    app = FastAPI()
    configure_production_app(app)

    @app.get("/failure")
    async def failure() -> None:
        raise HTTPException(status_code=404, detail="Missing resource")

    response = TestClient(app).get("/failure")
    body = response.json()

    assert response.status_code == 404
    assert body["error"]["code"] == "http_error"
    assert body["error"]["message"] == "Missing resource"
    assert body["error"]["request_id"]
