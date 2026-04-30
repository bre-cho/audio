#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORT_DIR="${ROOT_DIR}/artifacts/verify"
REPORT_FILE="${REPORT_DIR}/audio_production_verify_report.txt"
mkdir -p "${REPORT_DIR}"

echo "[verify_worker_e2e] start $(date -Iseconds)" >> "${REPORT_FILE}"
cd "${ROOT_DIR}/backend"
ARTIFACT_ROOT=/tmp/artifacts pytest -q tests/test_audio_worker_artifact_guard.py >> "${REPORT_FILE}" 2>&1

echo "[verify_worker_e2e] done $(date -Iseconds)" >> "${REPORT_FILE}"
