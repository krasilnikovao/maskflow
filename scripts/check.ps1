$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================="
Write-Host "MaskFlow Quality Check"
Write-Host "========================================="
Write-Host ""

# -----------------------------------------------------------------------------
# Ruff
# -----------------------------------------------------------------------------

Write-Host "[1/3] Ruff..."

ruff check .

if ($LASTEXITCODE -ne 0) {
    Write-Error "Ruff validation failed."
    exit 1
}

# -----------------------------------------------------------------------------
# MyPy
# -----------------------------------------------------------------------------

Write-Host ""
Write-Host "[2/3] MyPy..."

mypy .

if ($LASTEXITCODE -ne 0) {
    Write-Error "MyPy validation failed."
    exit 1
}

# -----------------------------------------------------------------------------
# Pytest
# -----------------------------------------------------------------------------

Write-Host ""
Write-Host "[3/3] Pytest..."

pytest

if ($LASTEXITCODE -ne 0) {
    Write-Error "Pytest failed."
    exit 1
}

Write-Host ""
Write-Host "========================================="
Write-Host "All checks passed."
Write-Host "========================================="
Write-Host ""