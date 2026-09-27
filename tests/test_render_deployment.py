import re

import pytest
from app.core.config import Settings


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "postgresql+asyncpg"])
def test_render_database_url(scheme):
    settings = Settings(_env_file=None, database_url=f"{scheme}://u:p%25@host/db")
    assert settings.database_url == "postgresql+asyncpg://u:p%25@host/db"


def test_production_rejects_default_secret():
    settings = Settings(_env_file=None, app_env="production")
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        settings.validate_production()


def test_production_rejects_debug():
    settings = Settings(_env_file=None, app_env="production", debug=True)
    with pytest.raises(RuntimeError, match="DEBUG=false"):
        settings.validate_production()


async def test_frontend_assets(client):
    assert (await client.get("/app")).status_code == 200
    assert (await client.get("/assets/app.js")).status_code == 200


async def test_root_serves_frontend_and_preserves_api(client, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    root = await client.get("/")
    assert root.status_code == 200
    assert root.headers["content-type"].startswith("text/html")
    assert root.text == (await client.get("/app")).text
    assets = re.findall(r'(?:src|href)="(/assets/[^\"]+)"', root.text)
    assert assets
    for asset in assets:
        response = await client.get(asset)
        assert response.status_code == 200
        assert response.content
    assert (await client.get("/docs")).status_code == 200
    schema = await client.get("/openapi.json")
    assert schema.status_code == 200
    assert "/api/v1/auth/login" in schema.json()["paths"]
    health = await client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"


async def test_unavailable_cv_storage(client, monkeypatch, tmp_path):
    from app.core.config import get_settings

    blocked = tmp_path / "not-a-directory"
    blocked.write_text("test")
    monkeypatch.setattr(get_settings(), "cv_storage_path", blocked / "cvs")
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": "storage@example.com", "password": "VerySecure123!"},
    )
    response = await client.post(
        "/api/v1/cvs",
        headers={"Authorization": f"Bearer {register.json()['access_token']}"},
        files={"file": ("cv.txt", b"Test CV", "text/plain")},
    )
    assert response.status_code == 503
