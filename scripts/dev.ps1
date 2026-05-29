$ErrorActionPreference = "Stop"

$env:MASKFLOW_DATA_DIR = if ($env:MASKFLOW_DATA_DIR) { $env:MASKFLOW_DATA_DIR } else { "data" }

New-Item -ItemType Directory -Force -Path `
    "$env:MASKFLOW_DATA_DIR/configs", `
    "$env:MASKFLOW_DATA_DIR/jobs", `
    "$env:MASKFLOW_DATA_DIR/reports", `
    "$env:MASKFLOW_DATA_DIR/tmp", `
    "$env:MASKFLOW_DATA_DIR/models" | Out-Null

uv run maskflow web --reload
