import pytest
from app.core.config import Settings, get_settings
from app.main import app
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_profile_and_preferences(client: AsyncClient) -> None:
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": "yasser@example.com", "password": "VerySecure123!"},
    )
    assert register.status_code == 201
    token = register.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    profile = await client.put(
        "/api/v1/profile",
        headers=headers,
        json={
            "full_name": "Yasser El Shafai",
            "email": "yasser@example.com",
            "phone": "+447300028668",
            "location": "Royal Tunbridge Wells, Kent",
            "years_experience": 22,
            "right_to_work_uk": True,
            "full_uk_driving_licence": True,
            "profile_data": {"max_sites": 156, "daily_delivery_orders": 7200},
        },
    )
    assert profile.status_code == 200
    assert profile.json()["profile_data"]["max_sites"] == 156

    preferences = await client.put(
        "/api/v1/preferences",
        headers=headers,
        json={
            "target_titles": ["Regional Operations Manager", "Head of Delivery"],
            "preferred_locations": ["London", "Kent"],
            "alternative_titles": ["Area Manager"],
            "work_arrangements": ["hybrid", "on-site"],
            "excluded_companies": ["Excluded Ltd"],
            "employment_types": ["full-time"],
            "willing_to_travel": True,
            "industries": ["QSR", "Hospitality", "Food Delivery"],
            "minimum_salary": 60000,
            "currency": "GBP",
            "requires_sponsorship": False,
        },
    )
    assert preferences.status_code == 200
    assert preferences.json()["alternative_titles"] == ["Area Manager"]
    assert preferences.json()["excluded_companies"] == ["Excluded Ltd"]
    assert preferences.json()["minimum_salary"] == 60000


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "VerySecure123!"},
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": "user@example.com", "password": "wrong"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_registration_returns_actionable_message(
    client: AsyncClient,
) -> None:
    payload = {"email": "duplicate@example.com", "password": "VerySecure123!"}
    created = await client.post("/api/v1/auth/register", json=payload)
    duplicate = await client.post("/api/v1/auth/register", json=payload)

    assert created.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["message"] == "Email is already registered"


@pytest.mark.asyncio
async def test_local_password_reset_then_login(client: AsyncClient) -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(
        app_env="development", local_password_reset_enabled=True
    )
    original = {"email": "reset@example.com", "password": "OriginalPass123!"}
    await client.post("/api/v1/auth/register", json=original)

    reset = await client.post(
        "/api/v1/auth/local-reset-password",
        json={"email": original["email"], "new_password": "NewSecurePass123!"},
    )
    assert reset.status_code == 200
    assert "Sign in" in reset.json()["message"]

    old_login = await client.post("/api/v1/auth/login", json=original)
    new_login = await client.post(
        "/api/v1/auth/login",
        json={"email": original["email"], "password": "NewSecurePass123!"},
    )
    assert old_login.status_code == 401
    assert new_login.status_code == 200
    assert new_login.json()["access_token"]


@pytest.mark.asyncio
async def test_local_password_reset_is_hidden_in_production(
    client: AsyncClient,
) -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(
        app_env="production", local_password_reset_enabled=True
    )
    response = await client.post(
        "/api/v1/auth/local-reset-password",
        json={"email": "nobody@example.com", "new_password": "NewSecurePass123!"},
    )
    assert response.status_code == 404
