param(
    [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Installing Sprint 11 into $ProjectRoot"

$copyItems = @(
    "backend\app\integrations\__init__.py",
    "backend\app\integrations\base.py",
    "backend\app\integrations\registry.py",
    "backend\app\integrations\remotive.py",
    "backend\app\integrations\email_notifier.py",
    "backend\app\schemas\integration.py",
    "backend\app\services\integration_service.py",
    "backend\app\api\routes\integrations.py",
    "tests\test_integration_registry.py",
    "tests\test_remotive_connector.py",
    "tests\test_email_notifier.py",
    "tests\test_integration_routes.py",
    "README_SPRINT11.md",
    "SPRINT11_MERGE.md"
)

foreach ($relative in $copyItems) {
    $source = Join-Path $SourceRoot $relative
    $destination = Join-Path $ProjectRoot $relative
    $destinationDir = Split-Path -Parent $destination
    New-Item -ItemType Directory -Force $destinationDir | Out-Null
    Copy-Item $source $destination -Force
}

$routerPath = Join-Path $ProjectRoot "backend\app\api\router.py"
$router = Get-Content $routerPath -Raw
if ($router -notmatch "integrations_router") {
    $router = $router -replace (
        "from fastapi import APIRouter\r?\n",
        "from fastapi import APIRouter`r`n`r`nfrom app.api.routes.integrations import router as integrations_router`r`n"
    )
    $router = $router.TrimEnd() + "`r`napi_router.include_router(integrations_router)`r`n"
    Set-Content $routerPath $router -Encoding utf8
}

Write-Host "Sprint 11 installed."
Write-Host "Next run:"
Write-Host '$env:PYTHONPATH="$PWD\backend"'
Write-Host 'python -m pytest --noconftest tests/test_integration_registry.py tests/test_remotive_connector.py tests/test_email_notifier.py tests/test_integration_routes.py'
