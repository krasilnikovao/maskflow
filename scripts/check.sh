#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"
PYTEST_RUNTIME_DIR="${PROJECT_ROOT}/.maskflow/pytest"
mkdir -p "${PYTEST_RUNTIME_DIR}"

echo
echo "========================================="
echo "MaskFlow Quality Check"
echo "========================================="
echo

echo "[1/3] Ruff..."
uv run --extra dev ruff check .

echo
echo "[2/3] MyPy..."
uv run --extra dev mypy .

echo
echo "[3/3] Pytest..."
uv run --extra dev pytest -o "cache_dir=${PYTEST_RUNTIME_DIR}/cache" --basetemp "${PYTEST_RUNTIME_DIR}/tmp-$$"

echo
echo "========================================="
echo "All checks passed."
echo "========================================="
