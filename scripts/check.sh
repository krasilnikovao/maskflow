#!/usr/bin/env bash
set -euo pipefail

echo
echo "========================================="
echo "MaskFlow Quality Check"
echo "========================================="
echo

echo "[1/3] Ruff..."
ruff check .

echo
echo "[2/3] MyPy..."
mypy .

echo
echo "[3/3] Pytest..."
pytest

echo
echo "========================================="
echo "All checks passed."
echo "========================================="
