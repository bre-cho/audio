#!/usr/bin/env bash
set -euo pipefail

MODE=${1:-smoke}
STEP=${2:-}
mkdir -p .verify_audio_e2e .audio_canary

TARGET_URL="${CANARY_BASE_URL:-${BASE_URL:-}}"
export BASE_URL="$TARGET_URL"

echo "[audio-canary] smoke mode=$MODE step=${STEP:-na} base_url=$BASE_URL" | tee -a .audio_canary/smoke.log

if [[ -n "${CANARY_HEALTH_URL:-}" ]]; then
  curl -fsS "$CANARY_HEALTH_URL" | tee .audio_canary/healthz.txt >/dev/null
fi

bash verify_audio_e2e.sh | tee -a .audio_canary/smoke.log
