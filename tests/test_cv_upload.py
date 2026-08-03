import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_and_list_cv(client: AsyncClient) -> None:
    register = await client.post("/api/v1/auth/register", json={"email": "cv@example.com", "password": "VerySecure123!"})
    headers = {"Authorization": f"Bearer {register.json()['access_token']}"}
    upload = await client.post(
        "/api/v1/cvs",
        headers=headers,
        data={"career_track": "operations"},
        files={"file": ("operations.pdf", b"%PDF-1.4 test", "application/pdf")},
    )
    assert upload.status_code == 201
    assert upload.json()["career_track"] == "operations"
    listing = await client.get("/api/v1/cvs", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1
