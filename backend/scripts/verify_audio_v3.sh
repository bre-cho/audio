#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

log(){ printf '\n[%s] %s\n' "$(date -u +%H:%M:%S)" "$*"; }

log "Checking fake queued routes"
if grep -R '"status"[[:space:]]*:[[:space:]]*"queued"' backend/app/api/bgm.py backend/app/api/sound_effects.py backend/app/api/transcription.py backend/app/api/localization.py backend/app/api/voice_changer.py 2>/dev/null; then
  echo "[FAIL] fake queued response remains in critical routes" >&2
  exit 1
fi

log "Running focused tests"
python -m pytest \
  backend/tests/test_no_fake_queued_routes.py \
  backend/tests/test_provider_single_source.py \
  backend/tests/test_voice_changer_provider_required.py \
  backend/tests/test_sfx_bgm_provider_gate.py \
  backend/tests/test_podcast_episode_builder.py

log "PASS audio production completion patch V3"
