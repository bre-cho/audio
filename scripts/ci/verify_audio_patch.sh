#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

API_SERVICE="${API_SERVICE:-api}"
WORKER_SERVICE="${WORKER_SERVICE:-worker}"
DOCKER_COMPOSE_BIN="${DOCKER_COMPOSE_BIN:-}"
REPORT_DIR="${REPORT_DIR:-${ROOT_DIR}/.verify_audio_patch}"
mkdir -p "$REPORT_DIR"
REPORT_FILE="$REPORT_DIR/report.txt"
: > "$REPORT_FILE"

FAILED=0
BASE_URL="${BASE_URL:-http://localhost:8000}"
VERIFY_RUNTIME="${VERIFY_RUNTIME:-1}"
ARTIFACT_ROOT_HOST="${ARTIFACT_ROOT:-${ROOT_DIR}/artifacts}"

log(){ echo "$*" | tee -a "$REPORT_FILE"; }
fail(){ log "FAIL: $*"; FAILED=$((FAILED+1)); }
ok(){ log "OK: $*"; }
trap 'fail "fatal error near line $LINENO"' ERR

run() {
  local desc="$1"; shift
  if "$@" >> "$REPORT_FILE" 2>&1; then
    ok "$desc"
  else
    fail "$desc"
  fi
}

resolve_compose_cmd() {
  if [[ -n "$DOCKER_COMPOSE_BIN" ]]; then
    # shellcheck disable=SC2206
    COMPOSE_CMD=($DOCKER_COMPOSE_BIN)
    return
  fi
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
    return
  fi
  if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
    return
  fi
  fail "docker compose command not found"
  exit 1
}

dc() {
  "${COMPOSE_CMD[@]}" "$@"
}

assert_file_exists() {
  local path="$1"
  [[ -f "$path" ]] && ok "file exists: $path" || fail "missing file: $path"
}

assert_no_legacy_concat() {
  if [[ ! -d backend/app/services/audio ]]; then
    ok "audio services folder absent"
    return
  fi
  if grep -R "combined_audio += audio_bytes" backend/app/services/audio -n >> "$REPORT_FILE" 2>&1; then
    fail "legacy byte-concat merge still present"
  else
    ok "legacy byte-concat merge absent"
  fi
}

assert_no_hardcoded_provider() {
  local search_paths=(backend/app/api)
  [[ -d backend/app/services/audio ]] && search_paths+=(backend/app/services/audio)
  if grep -R "ElevenLabsAdapter()" "${search_paths[@]}" -n >> "$REPORT_FILE" 2>&1; then
    fail "hardcoded ElevenLabsAdapter still present"
  else
    ok "no hardcoded ElevenLabsAdapter in audio route/service"
  fi
}

assert_contract_code_present() {
  assert_file_exists backend/app/services/audio_artifact_service.py
  assert_file_exists backend/app/audio_factory/factory_executor.py
  assert_file_exists backend/app/audio_factory/artifact_persistence.py
  grep -q "artifact_contract_version" backend/app/services/audio_artifact_service.py \
    && ok "artifact contract writer present" \
    || fail "artifact contract writer missing"
  grep -q "sha256" backend/app/services/audio_artifact_service.py \
    && ok "artifact checksum code present" \
    || fail "artifact checksum code missing"
  grep -q "promotion_gate" backend/app/audio_factory/job_finalizer.py \
    && ok "promotion gate runtime metadata present" \
    || fail "promotion gate runtime metadata missing"
  grep -q "StorageService" backend/app/services/audio_artifact_service.py \
    && ok "artifact writer uses StorageService" \
    || fail "artifact writer bypasses StorageService"
  grep -q "AudioFactoryExecutor" backend/app/workers/audio_tasks.py \
    && ok "audio output DB persistence delegated to factory executor" \
    || fail "audio output DB persistence delegation missing"
  grep -q "workflow_type" backend/app/models/audio_job.py \
    && ok "workflow_type persisted on audio jobs" \
    || fail "workflow_type missing on audio jobs"
  grep -q "contract_verified" backend/app/audio_factory/job_finalizer.py \
    && ok "truthful contract status present" \
    || fail "truthful contract status missing"
}

run "compile backend" python -m compileall backend/app
run "compile repo scripts" python -m compileall scripts

if timeout "${VERIFY_IMPORT_TIMEOUT:-45s}" env PYTHONPATH=backend python - <<'PY_IMPORTS' >> "$REPORT_FILE" 2>&1
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
PY_IMPORTS
then
  ok "audio modules import"
else
  fail "audio modules import"
fi

assert_no_legacy_concat
assert_no_hardcoded_provider
assert_contract_code_present
resolve_compose_cmd

if [[ "$VERIFY_RUNTIME" == "1" ]]; then
  SKIP_STACK_UP="${SKIP_STACK_UP:-0}"

  if [[ "$SKIP_STACK_UP" != "1" ]]; then
    run "docker compose up" dc up -d postgres redis api worker
  else
    ok "skip stack up"
  fi

  run "stack healthy" python scripts/ci/wait_for_stack.py 300

  if dc exec -T "$WORKER_SERVICE" celery \
    -A app.workers.celery_app.celery_app inspect ping --timeout=10 >> "$REPORT_FILE" 2>&1
  then
    ok "celery worker ready"
  else
    fail "celery worker not ready"
  fi

  if DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://postgres:postgres@localhost:5432/audio_ai}" PYTHONPATH=backend python scripts/migrations/audio_factory_schema.py >> "$REPORT_FILE" 2>&1
  then
    ok "audio factory schema migration"
  else
    fail "audio factory schema migration"
  fi

  if DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://postgres:postgres@localhost:5432/audio_ai}" PYTHONPATH=backend python scripts/ci/audio_schema_guard.py >> "$REPORT_FILE" 2>&1
  then
    ok "audio factory schema guard"
  else
    fail "audio factory schema guard"
  fi

  run "ffmpeg present" dc exec -T "$API_SERVICE" ffmpeg -version
  dc logs --tail=100 "$API_SERVICE" >> "$REPORT_FILE" 2>&1 || true
  dc logs --tail=100 "$WORKER_SERVICE" >> "$REPORT_FILE" 2>&1 || true

  mkdir -p "${ARTIFACT_ROOT_HOST}/audio"
  printf "probe" > "${ARTIFACT_ROOT_HOST}/audio/static-probe.txt"
  if curl -fsSI "$BASE_URL/artifacts/audio/static-probe.txt" >> "$REPORT_FILE" 2>&1; then
    ok "artifacts static route reachable"
  else
    fail "artifacts static route unreachable"
  fi
  rm -f "${ARTIFACT_ROOT_HOST}/audio/static-probe.txt"
else
  ok "runtime checks skipped"
fi

if [[ "$VERIFY_RUNTIME" == "1" && -d backend/tests ]]; then
  PYTHONPATH=backend pytest \
    backend/tests/test_audio_regression_guard.py \
    backend/tests/test_audio_route_task_mapping.py \
    backend/tests/test_audio_worker_artifact_guard.py \
    backend/tests/test_worker_retry_state_semantics.py \
    -q >> "$REPORT_FILE" 2>&1 \
    && ok "pytest audio guard tests" \
    || fail "pytest audio guard tests failed"
else
  ok "pytest runtime subset skipped"
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
