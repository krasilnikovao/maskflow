param(
    [ValidateSet("base", "dev", "download", "nlp", "qwen", "all")]
    [string]$Profile = "",

    [string[]]$Extras = @(),

    [switch]$NonInteractive,

    [switch]$SkipValidation
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..")
Push-Location $projectRoot

function Get-ProfileExtras {
    param([string]$SelectedProfile)

    switch ($SelectedProfile) {
        "base" { return @() }
        "dev" { return @("dev") }
        "download" { return @("download") }
        "nlp" { return @("download", "nlp") }
        "qwen" { return @("download", "nlp", "qwen") }
        "all" { return @("dev", "download", "nlp", "qwen") }
        default { return @("dev") }
    }
}

function Add-ExtraArgs {
    param([string[]]$SelectedExtras)

    $extraArgs = @()
    foreach ($extra in $SelectedExtras) {
        $extraArgs += "--extra"
        $extraArgs += $extra
    }
    return $extraArgs
}

function Read-ProfileSelection {
    Write-Host "Select installation profile:"
    Write-Host "  1) base      minimal runtime dependencies"
    Write-Host "  2) dev       development tools and tests"
    Write-Host "  3) download  model download support"
    Write-Host "  4) nlp       download + NLP providers"
    Write-Host "  5) qwen      download + NLP providers + Qwen"
    Write-Host "  6) all       dev + download + NLP + Qwen"
    Write-Host ""

    $selection = Read-Host "Profile [2]"
    if (-not $selection) {
        $selection = "2"
    }

    switch ($selection) {
        "1" { return "base" }
        "2" { return "dev" }
        "3" { return "download" }
        "4" { return "nlp" }
        "5" { return "qwen" }
        "6" { return "all" }
        "base" { return "base" }
        "dev" { return "dev" }
        "download" { return "download" }
        "nlp" { return "nlp" }
        "qwen" { return "qwen" }
        "all" { return "all" }
        default {
            Write-Error "Invalid profile selection: $selection"
            exit 1
        }
    }
}

function Read-YesNo {
    param(
        [string]$Prompt,
        [bool]$DefaultYes
    )

    $suffix = if ($DefaultYes) { "[Y/n]" } else { "[y/N]" }
    $answer = Read-Host "$Prompt $suffix"
    if (-not $answer) {
        return $DefaultYes
    }

    return $answer -match "^(y|yes)$"
}

try {
Write-Host ""
Write-Host "========================================="
Write-Host "MaskFlow Bootstrap"
Write-Host "========================================="
Write-Host ""

if (-not $Profile) {
    if ($NonInteractive) {
        $Profile = "dev"
    }
    else {
        $Profile = Read-ProfileSelection
    }
}

if (-not $NonInteractive -and -not $SkipValidation) {
    $SkipValidation = -not (Read-YesNo -Prompt "Run validation after install?" -DefaultYes $true)
}

# -----------------------------------------------------------------------------
# Проверка Python
# -----------------------------------------------------------------------------

Write-Host "[1/6] Checking Python..."

try {
    $pythonVersion = python --version
    Write-Host "Detected: $pythonVersion"
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Python 3.12+ is required."
        exit 1
    }
}
catch {
    Write-Error "Python 3.12+ is required."
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

$selectedExtras = @()
$selectedExtras += Get-ProfileExtras -SelectedProfile $Profile
$selectedExtras += $Extras
$selectedExtras = @($selectedExtras | Where-Object { $_ } | Select-Object -Unique)

$extraArgs = Add-ExtraArgs -SelectedExtras $selectedExtras
if ($selectedExtras.Count -gt 0) {
    Write-Host "Selected extras: $($selectedExtras -join ', ')"
}
else {
    Write-Host "Selected extras: none"
}

uv sync @extraArgs

# -----------------------------------------------------------------------------
# Runtime directories / env
# -----------------------------------------------------------------------------

$dataDir = if ($env:MASKFLOW_DATA_DIR) { $env:MASKFLOW_DATA_DIR } else { "data" }
New-Item -ItemType Directory -Force -Path `
    "$dataDir/configs", `
    "$dataDir/jobs", `
    "$dataDir/reports", `
    "$dataDir/tmp", `
    "$dataDir/models" | Out-Null

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example. Update secrets before production use."
}

# -----------------------------------------------------------------------------
# Проверка
# -----------------------------------------------------------------------------

Write-Host ""
Write-Host "[6/6] Running validation..."

python --version
uv --version

if (-not $SkipValidation -and ($selectedExtras -contains "dev")) {
    .\scripts\check.ps1
}
elseif (-not ($selectedExtras -contains "dev")) {
    Write-Host "Skipping validation because 'dev' extra is not installed."
}
else {
    Write-Host "Skipping validation by request."
}

Write-Host ""
Write-Host "========================================="
Write-Host "MaskFlow environment is ready."
Write-Host "========================================="
Write-Host ""
}
finally {
    Pop-Location
}
