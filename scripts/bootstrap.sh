#!/usr/bin/env bash
set -euo pipefail

PROFILE=""
EXTRAS=()
SKIP_VALIDATION=0
NON_INTERACTIVE=0

usage() {
  cat <<'USAGE'
Usage: ./scripts/bootstrap.sh [options]

Options:
  --profile base|dev|download|nlp|all   Dependency profile (default: dev)
  --extra NAME                          Add an extra dependency group
  --non-interactive                     Use defaults without prompts
  --skip-validation                     Do not run scripts/check.sh
  -h, --help                            Show this help

Profiles:
  base      no extras
  dev       dev
  download  download
  nlp       download,nlp
  all       dev,download,nlp
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="${2:-}"
      shift 2
      ;;
    --extra)
      EXTRAS+=("${2:-}")
      shift 2
      ;;
    --skip-validation)
      SKIP_VALIDATION=1
      shift
      ;;
    --non-interactive)
      NON_INTERACTIVE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

read_profile_selection() {
  echo "Select installation profile:"
  echo "  1) base      minimal runtime dependencies"
  echo "  2) dev       development tools and tests"
  echo "  3) download  model download support"
  echo "  4) nlp       download + NLP providers"
  echo "  5) all       dev + download + NLP"
  echo
  read -r -p "Profile [2]: " selection
  selection="${selection:-2}"

  case "${selection}" in
    1|base) echo "base" ;;
    2|dev) echo "dev" ;;
    3|download) echo "download" ;;
    4|nlp) echo "nlp" ;;
    5|all) echo "all" ;;
    *)
      echo "Invalid profile selection: ${selection}" >&2
      exit 1
      ;;
  esac
}

read_yes_no() {
  local prompt="$1"
  local default_yes="$2"
  local suffix="[y/N]"
  [[ "${default_yes}" == "1" ]] && suffix="[Y/n]"

  read -r -p "${prompt} ${suffix}: " answer
  if [[ -z "${answer}" ]]; then
    [[ "${default_yes}" == "1" ]]
    return
  fi

  [[ "${answer}" =~ ^([yY]|[yY][eE][sS])$ ]]
}

if [[ -z "${PROFILE}" ]]; then
  if [[ "${NON_INTERACTIVE}" -eq 1 || ! -t 0 ]]; then
    PROFILE="dev"
  else
    PROFILE="$(read_profile_selection)"
  fi
fi

if [[ "${NON_INTERACTIVE}" -eq 0 && "${SKIP_VALIDATION}" -eq 0 && -t 0 ]]; then
  if ! read_yes_no "Run validation after install?" 1; then
    SKIP_VALIDATION=1
  fi
fi

case "${PROFILE}" in
  base) PROFILE_EXTRAS=() ;;
  dev) PROFILE_EXTRAS=("dev") ;;
  download) PROFILE_EXTRAS=("download") ;;
  nlp) PROFILE_EXTRAS=("download" "nlp") ;;
  all) PROFILE_EXTRAS=("dev" "download" "nlp") ;;
  *)
    echo "Invalid profile: ${PROFILE}" >&2
    usage
    exit 1
    ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

echo
echo "========================================="
echo "MaskFlow Bootstrap"
echo "========================================="
echo

echo "[1/6] Checking Python..."
PYTHON_VERSION="$(python --version)"
echo "Detected: ${PYTHON_VERSION}"

if ! python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)'; then
  echo "Python 3.12+ is required." >&2
  exit 1
fi

echo
echo "[2/6] Checking uv..."
if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
fi
command -v uv >/dev/null 2>&1 || {
  echo "uv installation failed." >&2
  exit 1
}
echo "uv detected."

echo
echo "[3/6] Creating virtual environment..."
if [[ ! -d ".venv" ]]; then
  uv venv
else
  echo ".venv already exists."
fi

echo
echo "[4/6] Preparing dependency selection..."
SELECTED_EXTRAS=("${PROFILE_EXTRAS[@]}" "${EXTRAS[@]}")
UNIQUE_EXTRAS=()
for extra in "${SELECTED_EXTRAS[@]}"; do
  [[ -n "${extra}" ]] || continue
  found=0
  for existing in "${UNIQUE_EXTRAS[@]}"; do
    if [[ "${existing}" == "${extra}" ]]; then
      found=1
      break
    fi
  done
  [[ "${found}" -eq 1 ]] || UNIQUE_EXTRAS+=("${extra}")
done

EXTRA_ARGS=()
for extra in "${UNIQUE_EXTRAS[@]}"; do
  EXTRA_ARGS+=("--extra" "${extra}")
done

if [[ "${#UNIQUE_EXTRAS[@]}" -gt 0 ]]; then
  printf 'Selected extras: %s\n' "$(IFS=,; echo "${UNIQUE_EXTRAS[*]}")"
else
  echo "Selected extras: none"
fi

echo
echo "[5/6] Installing dependencies..."
uv sync "${EXTRA_ARGS[@]}"

DATA_DIR="${MASKFLOW_DATA_DIR:-data}"
mkdir -p \
  "${DATA_DIR}/configs" \
  "${DATA_DIR}/jobs" \
  "${DATA_DIR}/reports" \
  "${DATA_DIR}/tmp" \
  "${DATA_DIR}/models"

if [[ ! -f ".env" && -f ".env.example" ]]; then
  cp ".env.example" ".env"
  echo "Created .env from .env.example. Update secrets before production use."
fi

echo
echo "[6/6] Running validation..."
python --version
uv --version

HAS_DEV=0
for extra in "${UNIQUE_EXTRAS[@]}"; do
  if [[ "${extra}" == "dev" ]]; then
    HAS_DEV=1
    break
  fi
done

if [[ "${SKIP_VALIDATION}" -eq 0 && "${HAS_DEV}" -eq 1 ]]; then
  ./scripts/check.sh
elif [[ "${HAS_DEV}" -eq 0 ]]; then
  echo "Skipping validation because 'dev' extra is not installed."
else
  echo "Skipping validation by request."
fi

echo
echo "========================================="
echo "MaskFlow environment is ready."
echo "========================================="
echo
