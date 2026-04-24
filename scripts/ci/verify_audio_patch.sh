#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

API_SERVICE="${API_SERVICE:-api}"
WORKER_SERVICE="${WORKER_SERVICE:-worker}"
DOCKER_COMPOSE_BIN="${DOCKER_COMPOSE_BIN:-docker compose}"
REPORT_DIR="${ROOT_DIR}/.verify_audio_patch"
mkdir -p "$REPORT_DIR"
REPORT_FILE="$REPORT_DIR/report.txt"
: > "$REPORT_FILE"

pass=true
log(){ echo "$*" | tee -a "$REPORT_FILE"; }
fail(){ log "FAIL: $*"; pass=false; }
ok(){ log "OK: $*"; }

python -m compileall backend/app >> "$REPORT_FILE" 2>&1 || fail "compileall failed"
python - <<'PY' >> "$REPORT_FILE" 2>&1 || exit 7
import importlib
mods=[
  'backend.app.api.audio',
  'backend.app.services.tts_service',
  'backend.app.services.voice_clone_service',
  'backend.app.workers.audio_tasks',
]
for m in mods:
    importlib.import_module(m)
    print('OK', m)
PY
[[ $? -eq 0 ]] && ok "audio modules import" || fail "audio modules import"

grep -R "combined_audio += audio_bytes" backend/app/services/audio -n >> "$REPORT_FILE" 2>&1 && fail "legacy byte-concat merge still present" || ok "legacy byte-concat merge absent"
grep -R "ElevenLabsAdapter()" backend/app/api backend/app/services/audio -n >> "$REPORT_FILE" 2>&1 && fail "hardcoded ElevenLabsAdapter still present" || ok "no hardcoded ElevenLabsAdapter in audio route/service"

$DOCKER_COMPOSE_BIN up -d >> "$REPORT_FILE" 2>&1 || fail "docker compose up failed"
$DOCKER_COMPOSE_BIN exec -T "$API_SERVICE" ffmpeg -version >> "$REPORT_FILE" 2>&1 || fail "ffmpeg missing in api container"
$DOCKER_COMPOSE_BIN logs --tail=100 "$API_SERVICE" >> "$REPORT_FILE" 2>&1 || true
$DOCKER_COMPOSE_BIN logs --tail=100 "$WORKER_SERVICE" >> "$REPORT_FILE" 2>&1 || true

if [[ -d backend/tests ]]; then
  pytest -q -k "audio or narration or voice_clone" >> "$REPORT_FILE" 2>&1 || fail "pytest audio subset failed"
else
  log "OK: backend/tests not found; skipping pytest for bootstrap phase"
fi

if [[ "$pass" == "true" ]]; then
  log "GO"
  exit 0
else
  log "NO-GO"
  exit 1
fi
