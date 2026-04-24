#!/usr/bin/env bash
set -euo pipefail

mkdir -p .audio_canary

echo "[audio-canary] rollback to stable revision: ${STABLE_REVISION:-unknown}" | tee -a .audio_canary/rollback.log
bash -lc "$ROLLBACK_COMMAND" | tee -a .audio_canary/rollback.log
