$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..")
$pytestRuntimeDir = Join-Path $projectRoot ".maskflow/pytest"
$pytestCacheDir = Join-Path $pytestRuntimeDir "cache"
$pytestTempDir = Join-Path $pytestRuntimeDir "tmp-$PID"

New-Item -ItemType Directory -Force -Path $pytestRuntimeDir | Out-Null

Push-Location $projectRoot

try {
Write-Host ""
Write-Host "========================================="
Write-Host "MaskFlow Quality Check"
Write-Host "========================================="
Write-Host ""

# -----------------------------------------------------------------------------
# Ruff
# -----------------------------------------------------------------------------

Write-Host "[1/3] Ruff..."

uv run --extra dev ruff check .

if ($LASTEXITCODE -ne 0) {
    Write-Error "Ruff validation failed."
    exit 1
}

# -----------------------------------------------------------------------------
# MyPy
# -----------------------------------------------------------------------------

Write-Host ""
Write-Host "[2/3] MyPy..."

uv run --extra dev mypy .

if ($LASTEXITCODE -ne 0) {
    Write-Error "MyPy validation failed."
    exit 1
}

# -----------------------------------------------------------------------------
# Pytest
# -----------------------------------------------------------------------------

Write-Host ""
Write-Host "[3/3] Pytest..."

uv run --extra dev pytest -o "cache_dir=$pytestCacheDir" --basetemp "$pytestTempDir"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Pytest failed."
    exit 1
}

Write-Host ""
Write-Host "========================================="
Write-Host "All checks passed."
Write-Host "========================================="
Write-Host ""
}
finally {
    Pop-Location
}
