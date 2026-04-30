#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORT_DIR="${ROOT_DIR}/artifacts/verify"
REPORT_FILE="${REPORT_DIR}/audio_production_verify_report.txt"
mkdir -p "${REPORT_DIR}"

echo "[verify_p2_engines] start $(date -Iseconds)" >> "${REPORT_FILE}"

cd "${ROOT_DIR}/backend"
export ARTIFACT_ROOT="${ARTIFACT_ROOT:-/tmp/artifacts}"

pytest -q tests/test_p2_engines.py >> "${REPORT_FILE}" 2>&1

PYTHONPATH=. python - <<'PY' >> "${REPORT_FILE}" 2>&1
from app.audio_engines.noise_reducer.noise_pipeline import NOISE_PROFILES
from app.audio_engines.enhancer.enhancement_pipeline import VOICE_PROFILES

assert "balanced" in NOISE_PROFILES
assert "broadcast" in VOICE_PROFILES
print("p2 profile registry verified")
PY

echo "[verify_p2_engines] done $(date -Iseconds)" >> "${REPORT_FILE}"
