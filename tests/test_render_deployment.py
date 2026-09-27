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
