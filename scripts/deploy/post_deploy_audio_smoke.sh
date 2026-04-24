#!/usr/bin/env bash
set -Eeuo pipefail

log(){ printf '%s %s\n' "[$(date '+%Y-%m-%d %H:%M:%S')]" "$*"; }

BASE_URL="${BASE_URL:-}"
AUDIO_HEALTH_URL="${AUDIO_HEALTH_URL:-}"

if [[ -n "$AUDIO_HEALTH_URL" ]]; then
  log "Checking AUDIO_HEALTH_URL=$AUDIO_HEALTH_URL"
  curl -fsS "$AUDIO_HEALTH_URL" >/dev/null
fi

if [[ ! -f ./verify_audio_e2e.sh && ! -f scripts/ci/verify_audio_e2e.sh ]]; then
  log "verify_audio_e2e.sh not found"
  exit 1
fi

if [[ -f ./verify_audio_e2e.sh ]]; then
  chmod +x ./verify_audio_e2e.sh || true
  ./verify_audio_e2e.sh
else
  chmod +x scripts/ci/verify_audio_e2e.sh || true
  bash scripts/ci/verify_audio_e2e.sh
fi
