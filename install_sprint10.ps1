param(
    [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Installing Sprint 10 into $ProjectRoot"

$copyItems = @(
    "backend\alembic\versions\20260809_0007_application_workflows.py",
    "backend\app\models\application_workflow.py",
    "backend\app\schemas\application_workflow.py",
    "backend\app\services\application_workflow.py",
    "backend\app\api\routes\applications.py",
    "tests\test_application_workflow.py",
    "tests\test_application_routes.py",
    "README_SPRINT10.md",
    "SPRINT10_MERGE.md"
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

if ($router -notmatch "applications_router") {
    $router = $router -replace (
        "from fastapi import APIRouter\r?\n",
        "from fastapi import APIRouter`r`n`r`nfrom app.api.routes.applications import router as applications_router`r`n"
    )
    $router = $router.TrimEnd() + "`r`napi_router.include_router(applications_router)`r`n"
    Set-Content $routerPath $router -Encoding utf8
}

$modelsPath = Join-Path $ProjectRoot "backend\app\models\__init__.py"
$models = Get-Content $modelsPath -Raw

if ($models -notmatch "application_workflow") {
    $models = "from app.models.application_workflow import ApplicationWorkflow`r`n" + $models
}

if ($models -match "__all__\s*=\s*\[(.*?)\]") {
    if ($models -notmatch '"ApplicationWorkflow"') {
        $models = $models -replace (
            "__all__\s*=\s*\[",
            '__all__ = ["ApplicationWorkflow", '
        )
    }
}

Set-Content $modelsPath $models -Encoding utf8

Write-Host "Sprint 10 installed."
Write-Host "Next run:"
Write-Host '$env:PYTHONPATH="$PWD\backend"'
Write-Host 'python -m pytest --noconftest tests/test_application_workflow.py tests/test_application_routes.py'
