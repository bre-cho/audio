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

FAILED=0
BASE_URL="${BASE_URL:-http://localhost:8000}"
log(){ echo "$*" | tee -a "$REPORT_FILE"; }
fail(){ log "FAIL: $*"; FAILED=$((FAILED+1)); }
ok(){ log "OK: $*"; }

python -m compileall backend/app >> "$REPORT_FILE" 2>&1 || fail "compileall failed"
if PYTHONPATH=backend python - <<'PY' >> "$REPORT_FILE" 2>&1
import importlib

mods = [
    "app.api.audio",
    "app.api.jobs",
    "app.api.voice_clone",
    "app.services.tts_service",
    "app.services.voice_clone_service",
    "app.services.audio_artifact_service",
    "app.workers.audio_tasks",
    "app.workers.clone_tasks",
]

for mod in mods:
    importlib.import_module(mod)
    print("OK", mod)
PY
then
  ok "audio modules import"
else
  fail "audio modules import"
fi

grep -R "combined_audio += audio_bytes" backend/app/services/audio -n >> "$REPORT_FILE" 2>&1 && fail "legacy byte-concat merge still present" || ok "legacy byte-concat merge absent"
grep -R "ElevenLabsAdapter()" backend/app/api backend/app/services/audio -n >> "$REPORT_FILE" 2>&1 && fail "hardcoded ElevenLabsAdapter still present" || ok "no hardcoded ElevenLabsAdapter in audio route/service"

$DOCKER_COMPOSE_BIN up -d postgres redis api worker >> "$REPORT_FILE" 2>&1 || fail "docker compose up failed"
$DOCKER_COMPOSE_BIN exec -T "$API_SERVICE" ffmpeg -version >> "$REPORT_FILE" 2>&1 || fail "ffmpeg missing in api container"
$DOCKER_COMPOSE_BIN logs --tail=100 "$API_SERVICE" >> "$REPORT_FILE" 2>&1 || true
$DOCKER_COMPOSE_BIN logs --tail=100 "$WORKER_SERVICE" >> "$REPORT_FILE" 2>&1 || true

if curl -fsSI "$BASE_URL/artifacts/" >> "$REPORT_FILE" 2>&1; then
  ok "artifacts static route reachable"
else
  fail "artifacts static route reachable"
fi

if [[ -d backend/tests ]]; then
  pytest -q -k "audio or narration or voice_clone" >> "$REPORT_FILE" 2>&1 || fail "pytest audio subset failed"
else
  log "OK: backend/tests not found; skipping pytest for bootstrap phase"
fi

echo
echo "==== AUDIO PATCH VERIFY REPORT ===="
cat "$REPORT_FILE"

if [[ "$FAILED" -eq 0 ]]; then
  echo "GO"
  exit 0
else
  echo "NO-GO"
  exit 1
fi
