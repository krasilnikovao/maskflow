$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================="
Write-Host "MaskFlow Bootstrap"
Write-Host "========================================="
Write-Host ""

# -----------------------------------------------------------------------------
# Проверка Python
# -----------------------------------------------------------------------------

Write-Host "[1/6] Checking Python..."

try {
    $pythonVersion = python --version
    Write-Host "Detected: $pythonVersion"
}
catch {
    Write-Error "Python 3.12+ is required."
    exit 1
}

if ($pythonVersion -notmatch "3\.12") {
    Write-Error "Python 3.12 is required."
    exit 1
}

# -----------------------------------------------------------------------------
# Проверка uv
# -----------------------------------------------------------------------------

Write-Host ""
Write-Host "[2/6] Checking uv..."

$uvExists = Get-Command uv -ErrorAction SilentlyContinue

if (-not $uvExists) {

    Write-Host "uv not found."
    Write-Host "Installing uv..."

    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

    $env:Path += ";$HOME\.local\bin"

    $uvExists = Get-Command uv -ErrorAction SilentlyContinue

    if (-not $uvExists) {
        Write-Error "uv installation failed."
        exit 1
    }
}

Write-Host "uv detected."

# -----------------------------------------------------------------------------
# Создание venv
# -----------------------------------------------------------------------------

Write-Host ""
Write-Host "[3/6] Creating virtual environment..."

if (-not (Test-Path ".venv")) {
    uv venv
}
else {
    Write-Host ".venv already exists."
}

# -----------------------------------------------------------------------------
# Активация venv
# -----------------------------------------------------------------------------

Write-Host ""
Write-Host "[4/6] Activating virtual environment..."

& ".\.venv\Scripts\Activate.ps1"

# -----------------------------------------------------------------------------
# Установка зависимостей
# -----------------------------------------------------------------------------

Write-Host ""
Write-Host "[5/6] Installing dependencies..."

uv sync --extra dev

# -----------------------------------------------------------------------------
# Проверка
# -----------------------------------------------------------------------------

Write-Host ""
Write-Host "[6/6] Running validation..."

python --version
uv --version

Write-Host ""
Write-Host "========================================="
Write-Host "MaskFlow environment is ready."
Write-Host "========================================="
Write-Host ""