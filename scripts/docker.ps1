$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..")
$composeFile = Join-Path $projectRoot "docker/docker-compose.yml"
$envFile = Join-Path $projectRoot ".env"
$dataDir = Join-Path $projectRoot "data"
$legacyProjectName = "docker"

if (-not (Test-Path $envFile)) {
    Write-Error "Missing .env file: $envFile"
    exit 1
}

$envValues = @{}
Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
        return
    }

    $key, $value = $line.Split("=", 2)
    $envValues[$key.Trim()] = $value.Trim()
}

$nlpAutoDownload = $envValues["MASKFLOW_NLP_AUTO_DOWNLOAD"] -match "^(1|true|yes|on)$"
$extras = $envValues["MASKFLOW_EXTRAS"]
if ($nlpAutoDownload -and ($extras -notmatch "(^|,)download(,|$)")) {
    Write-Error "MASKFLOW_NLP_AUTO_DOWNLOAD=true requires MASKFLOW_EXTRAS to include 'download'. Example: MASKFLOW_EXTRAS=download,nlp"
    exit 1
}

Push-Location $projectRoot

try {
    New-Item -ItemType Directory -Force -Path `
        (Join-Path $dataDir "configs"), `
        (Join-Path $dataDir "jobs"), `
        (Join-Path $dataDir "reports"), `
        (Join-Path $dataDir "tmp"), `
        (Join-Path $dataDir "models") | Out-Null

    Write-Host "Stopping legacy compose project '$legacyProjectName' if it exists..."
    docker compose -p $legacyProjectName -f $composeFile down --remove-orphans
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to stop legacy compose project '$legacyProjectName'."
        exit $LASTEXITCODE
    }

    Write-Host "Building and starting MaskFlow in detached mode..."
    docker compose --env-file $envFile -f $composeFile up --build -d
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker Compose failed. Check the build output above and verify port 3100 is free."
        exit $LASTEXITCODE
    }
}
finally {
    Pop-Location
}

Write-Host "MaskFlow container started in detached mode."
Write-Host "Web UI: http://127.0.0.1:3100"
Write-Host "Logs: docker compose --env-file `"$envFile`" -f `"$composeFile`" logs -f"
