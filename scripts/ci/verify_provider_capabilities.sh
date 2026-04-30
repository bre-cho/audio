#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORT_DIR="${ROOT_DIR}/artifacts/verify"
REPORT_FILE="${REPORT_DIR}/audio_production_verify_report.txt"
mkdir -p "${REPORT_DIR}"

echo "[verify_provider_capabilities] start $(date -Iseconds)" >> "${REPORT_FILE}"

cd "${ROOT_DIR}"
PYTHONPATH=backend python - <<'PY' >> "${REPORT_FILE}" 2>&1
from app.providers.capability_registry import CAPABILITIES, ENGINE_CAPABILITIES

assert CAPABILITIES["internal_genvoice"].production_ready is False
assert CAPABILITIES["minimax"].production_ready is False
assert CAPABILITIES["elevenlabs"].production_ready is True
assert ENGINE_CAPABILITIES["noise_reduction"]["status"] == "active"
assert ENGINE_CAPABILITIES["voice_enhancement"]["status"] == "active"
assert ENGINE_CAPABILITIES["podcast_mix"]["status"] == "active"
assert ENGINE_CAPABILITIES["noise_reduction"]["provider_required"] is False
assert ENGINE_CAPABILITIES["voice_enhancement"]["provider_required"] is False
assert ENGINE_CAPABILITIES["podcast_mix"]["provider_required"] is False
print("provider capability matrix verified")
PY

echo "[verify_provider_capabilities] done $(date -Iseconds)" >> "${REPORT_FILE}"
