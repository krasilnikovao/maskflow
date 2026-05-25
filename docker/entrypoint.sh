#!/usr/bin/env sh
set -eu

mkdir -p \
  "${MASKFLOW_DATA_DIR:-/data}/configs" \
  "${MASKFLOW_DATA_DIR:-/data}/jobs" \
  "${MASKFLOW_DATA_DIR:-/data}/reports" \
  "${MASKFLOW_DATA_DIR:-/data}/tmp"

exec maskflow "$@"
