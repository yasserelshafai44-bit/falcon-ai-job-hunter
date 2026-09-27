import shutil
import subprocess
from pathlib import Path

import pytest


def test_cv_discovery_frontend_state():
    node = shutil.which("node")
    assert node, "Node.js is required for the CV discovery regression"
    result = subprocess.run(
        [node, str(Path(__file__).with_name("frontend_cv_discovery.mjs"))],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.asyncio
async def test_persisted_analysis_discovered_without_profile_or_upload_file(
    client,
    monkeypatch,
    tmp_path,
):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "cv_storage_path", tmp_path / "uploads")
    credentials = {"email": "cv-discovery@example.com", "password": "SecurePass123!"}
    registration = await client.post("/api/v1/auth/register", json=credentials)
    headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}
    upload = await client.post(
        "/api/v1/cvs",
        headers=headers,
        files={
            "file": (
                "cv.txt",
                b"Operations manager with team leadership and "
                b"multi-site operations experience.",
                "text/plain",
            )
        },
    )
    assert upload.status_code == 201
    cv_id = upload.json()["id"]
    analysis = await client.post(
        f"/api/v1/candidate-intelligence/cvs/{cv_id}/analyze",
        headers=headers,
    )
    assert analysis.status_code == 200
    analysis_id = analysis.json()["id"]
    assert analysis.json()["analysis"]["skills"]
    assert (await client.get("/api/v1/profile", headers=headers)).status_code == 404

    # Simulate a new session after Render has lost the temporary upload directory.
    monkeypatch.setattr(get_settings(), "cv_storage_path", tmp_path / "empty")
    login = await client.post("/api/v1/auth/login", json=credentials)
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    cvs = await client.get("/api/v1/cvs", headers=headers)
    assert cvs.json()[0]["id"] == cv_id
    restored = await client.get(
        f"/api/v1/candidate-intelligence/cvs/{cv_id}",
        headers=headers,
    )
    assert restored.status_code == 200
    assert restored.json()["id"] == analysis_id
    synced = await client.post(
        "/api/v1/jobs/sync",
        headers=headers,
        json={
            "providers": ["local"],
            "limit_per_provider": 1,
            "candidate_analysis_id": analysis_id,
        },
    )
    assert synced.status_code == 200
    matches = (await client.get("/api/v1/matches", headers=headers)).json()["items"]
    assert matches
    assert all(row["candidate_analysis_id"] == analysis_id for row in matches)

    other = await client.post(
        "/api/v1/auth/register",
        json={**credentials, "email": "another-candidate@example.com"},
    )
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    private = await client.get(
        f"/api/v1/candidate-intelligence/cvs/{cv_id}",
        headers=other_headers,
    )
    assert private.status_code == 404
    denied = await client.post(
        f"/api/v1/matches/jobs/{matches[0]['job_id']}/score",
        headers=other_headers,
        json={"candidate_analysis_id": analysis_id},
    )
    assert denied.status_code == 404
