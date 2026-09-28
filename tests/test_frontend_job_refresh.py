import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_refresh_ui_has_visible_progress_and_error_contract(
    client: AsyncClient,
) -> None:
    page = await client.get("/app")
    script = await client.get("/assets/app.js")

    assert page.status_code == 200
    assert '/assets/app.js?v=20260928-ranking-timeout' in page.text
    assert 'id="refreshRankJobs"' in page.text
    assert 'id="jobRefreshStatus" role="status" aria-live="polite"' in page.text
    assert "setJobRefreshState('Contacting verified employers" in script.text
    assert "Your session expired. Please sign in again" in script.text
    assert "Unable to refresh and rank jobs:" in script.text
    assert "No current vacancies were returned" in script.text
    assert "Promise.allSettled" in script.text
    assert "const RANKING_TIMEOUT_MS=120000" in script.text
    assert "new AbortController()" in script.text
    assert "Ranking timed out after 2 minutes" in script.text
    assert "Try a narrower employer selection or retry" in script.text
    assert "loadEmployerRegistry(controller.signal)" in script.text
    assert 'id="clearJobFilters"' in page.text
    assert 'id="jobFilterSummary"' in page.text
    assert "function applyJobFilters()" in script.text
    assert "ranked vacancies shown" in script.text
    assert "All recommendations including Reject" in script.text
    assert "liveEmployerEntries.filter(item=>item.status==='LIVE'" in script.text


@pytest.mark.asyncio
async def test_refresh_ui_uses_server_resolved_all_and_individual_providers(
    client: AsyncClient,
) -> None:
    page = await client.get("/app")
    script = await client.get("/assets/app.js")

    assert '<option value="all_verified_direct">' in page.text
    assert '<option value="deliveroo">' in page.text
    assert "const refreshedProviders=sync.providers_requested||[]" in script.text
    assert "const persisted=await request('/matches',{signal:controller.signal})" in script.text
    assert "jobs.map(job=>request(`/matches/jobs/" not in script.text


@pytest.mark.asyncio
async def test_refresh_api_rejects_invalid_authentication(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/jobs/sync",
        headers={"Authorization": "Bearer invalid-token"},
        json={"providers": ["all_verified_direct"]},
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid token"


def test_frontend_filter_behaviour() -> None:
    """Run the real JavaScript filter logic, including browser-restored controls."""
    import shutil
    import subprocess
    from pathlib import Path

    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is required for frontend behavioral tests")
    result = subprocess.run(
        [node, str(Path(__file__).with_name("frontend_job_filters.mjs"))],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
