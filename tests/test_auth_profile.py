import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_profile_and_preferences(client: AsyncClient) -> None:
    register = await client.post("/api/v1/auth/register", json={"email": "yasser@example.com", "password": "VerySecure123!"})
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
            "work_arrangements": ["hybrid", "on-site"],
            "industries": ["QSR", "Hospitality", "Food Delivery"],
            "minimum_salary": 60000,
            "currency": "GBP",
            "requires_sponsorship": False,
        },
    )
    assert preferences.status_code == 200
    assert preferences.json()["minimum_salary"] == 60000


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json={"email": "user@example.com", "password": "VerySecure123!"})
    response = await client.post("/api/v1/auth/login", json={"email": "user@example.com", "password": "wrong"})
    assert response.status_code == 401
