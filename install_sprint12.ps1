param(
    [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Installing Sprint 12 into $ProjectRoot"

$copyItems = @(
    "backend\app\services\job_hunt_orchestrator.py",
    "tests\test_job_hunt_orchestrator.py",
    "README_SPRINT12.md",
    "SPRINT12_MERGE.md"
)

foreach ($relative in $copyItems) {
    $source = Join-Path $SourceRoot $relative
    $destination = Join-Path $ProjectRoot $relative
    $destinationDir = Split-Path -Parent $destination
    New-Item -ItemType Directory -Force $destinationDir | Out-Null
    Copy-Item $source $destination -Force
}

Write-Host "Sprint 12 installed."
Write-Host "Next run:"
Write-Host '$env:PYTHONPATH="$PWD\backend"'
Write-Host 'python -m pytest --noconftest tests/test_job_hunt_orchestrator.py'
