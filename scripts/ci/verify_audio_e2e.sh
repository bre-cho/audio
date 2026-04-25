#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

BASE_URL="${BASE_URL:-http://localhost:8000}"
API_SERVICE="${API_SERVICE:-api}"
WORKER_SERVICE="${WORKER_SERVICE:-worker}"
DOCKER_COMPOSE_BIN="${DOCKER_COMPOSE_BIN:-docker compose}"
AUTH_ENABLED="${AUTH_ENABLED:-0}"
AUTH_EMAIL="${AUTH_EMAIL:-}"
AUTH_PASSWORD="${AUTH_PASSWORD:-}"
REPORT_DIR="${REPORT_DIR:-$ROOT_DIR/.verify_audio_e2e}"
mkdir -p "$REPORT_DIR"
REPORT_FILE="$REPORT_DIR/report.txt"
PREVIEW_STATUS_FILE="$REPORT_DIR/audio_preview_job_status.json"
NARRATION_STATUS_FILE="$REPORT_DIR/audio_narration_job_status.json"
: > "$REPORT_FILE"

pass=true
AUTH_ARGS=()
PROJECT_ID=""
PREVIEW_JOB_ID=""
NARRATION_JOB_ID=""
PREVIEW_POLL_ATTEMPTS="${PREVIEW_POLL_ATTEMPTS:-40}"
NARRATION_POLL_ATTEMPTS="${NARRATION_POLL_ATTEMPTS:-12}"
RUN_NARRATION_E2E="${RUN_NARRATION_E2E:-0}"

log(){ echo "$*" | tee -a "$REPORT_FILE"; }
fail(){ log "FAIL: $*"; pass=false; }
ok(){ log "OK: $*"; }
trap 'fail "fatal error near line $LINENO"' ERR

json_get() {
  local path="$1"
  python -c '
import json, sys
path = sys.argv[1]
try:
  data = json.load(sys.stdin)
except Exception:
  print("")
  raise SystemExit(0)
cur = data
for part in path.split("."):
  if part.endswith("]") and "[" in part:
    name, idx = part[:-1].split("[", 1)
    if name:
      cur = cur.get(name) if isinstance(cur, dict) else None
    try:
      cur = cur[int(idx)] if isinstance(cur, list) else None
    except Exception:
      cur = None
  elif isinstance(cur, dict):
    cur = cur.get(part)
  else:
    cur = None
  if cur is None:
    break
if isinstance(cur, (dict, list)):
  print(json.dumps(cur, separators=(",", ":")))
else:
  print("" if cur is None else cur)
' "$path"
}

assert_not_empty() {
  local value="$1"; local msg="$2"
  [[ -n "$value" && "$value" != "null" ]] && ok "$msg" || fail "$msg"
}

assert_json_key() {
  local json="$1"; local key="$2"; local msg="${3:-json key exists: $key}"
  local value
  value="$(printf '%s' "$json" | json_get "$key")"
  assert_not_empty "$value" "$msg"
}

assert_http_head_audio() {
  local url="$1"; local label="$2"
  local headers content_type content_length
  if ! headers="$(curl -fsSI "$BASE_URL$url" 2>>"$REPORT_FILE")"; then
    fail "$label artifact not reachable: $url"
    return
  fi
  ok "$label artifact reachable: $url"
  content_type="$(printf '%s' "$headers" | awk -F': ' 'tolower($1)=="content-type"{print tolower($2)}' | tr -d '\r' | tail -1)"
  content_length="$(printf '%s' "$headers" | awk -F': ' 'tolower($1)=="content-length"{print $2}' | tr -d '\r' | tail -1)"
  [[ "$content_type" == *audio* ]] && ok "$label content-type audio: $content_type" || fail "$label content-type not audio: $content_type"
  if [[ -n "$content_length" ]]; then
    [[ "$content_length" =~ ^[0-9]+$ && "$content_length" -gt 0 ]] && ok "$label content-length > 0" || fail "$label invalid content-length: $content_length"
  fi
}

assert_artifact_contract() {
  local artifact="$1"; local prefix="$2"
  for key in artifact_id artifact_type url mime_type size_bytes checksum created_at source_job_id input_hash provider template_version runtime_version write_integrity_pass contract_pass lineage_pass replayability_pass determinism_pass drift_budget_pass promotion_status; do
    assert_json_key "$artifact" "$key" "$prefix artifact key exists: $key"
  done
  local size checksum status contract_pass lineage_pass write_integrity_pass
  size="$(printf '%s' "$artifact" | json_get size_bytes)"
  checksum="$(printf '%s' "$artifact" | json_get checksum)"
  status="$(printf '%s' "$artifact" | json_get promotion_status)"
  contract_pass="$(printf '%s' "$artifact" | json_get contract_pass)"
  lineage_pass="$(printf '%s' "$artifact" | json_get lineage_pass)"
  write_integrity_pass="$(printf '%s' "$artifact" | json_get write_integrity_pass)"
  [[ "$size" =~ ^[0-9]+$ && "$size" -gt 0 ]] && ok "$prefix artifact size_bytes valid" || fail "$prefix artifact size_bytes invalid: $size"
  [[ "$checksum" =~ ^[a-fA-F0-9]{64}$ ]] && ok "$prefix artifact checksum sha256-like" || fail "$prefix artifact checksum invalid"
  [[ "$contract_pass" == "True" || "$contract_pass" == "true" ]] && ok "$prefix artifact contract_pass=true" || fail "$prefix artifact contract_pass invalid: $contract_pass"
  [[ "$lineage_pass" == "True" || "$lineage_pass" == "true" ]] && ok "$prefix artifact lineage_pass=true" || fail "$prefix artifact lineage_pass invalid: $lineage_pass"
  [[ "$write_integrity_pass" == "True" || "$write_integrity_pass" == "true" ]] && ok "$prefix artifact write_integrity_pass=true" || fail "$prefix artifact write_integrity_pass invalid: $write_integrity_pass"
  [[ "$status" == "contract_verified" || "$status" == "promoted" ]] && ok "$prefix artifact promotion status accepted: $status" || fail "$prefix artifact invalid promotion_status: $status"
  local url
  url="$(printf '%s' "$artifact" | json_get url)"
  assert_http_head_audio "$url" "$prefix"
}

assert_job_artifacts() {
  local job_json="$1"
  assert_json_key "$job_json" "runtime_json.artifacts[0]" "job has first artifact"
  assert_json_key "$job_json" "runtime_json.artifacts[1]" "job has second artifact"
  local artifact0 artifact1
  artifact0="$(printf '%s' "$job_json" | json_get runtime_json.artifacts[0])"
  artifact1="$(printf '%s' "$job_json" | json_get runtime_json.artifacts[1])"
  assert_artifact_contract "$artifact0" "preview"
  assert_artifact_contract "$artifact1" "output"
  for key in contract_pass lineage_pass write_integrity_pass replayability_pass determinism_pass drift_budget_pass promotion_status checked_at; do
    assert_json_key "$job_json" "runtime_json.promotion_gate.$key" "promotion gate key exists: $key"
  done
}

SKIP_STACK_UP="${SKIP_STACK_UP:-0}"
if [[ "$SKIP_STACK_UP" != "1" ]]; then
  $DOCKER_COMPOSE_BIN up -d postgres redis api worker >> "$REPORT_FILE" 2>&1 || fail "docker compose up failed"
else
  ok "skip stack up"
fi
python scripts/ci/wait_for_stack.py 300 >> "$REPORT_FILE" 2>&1 || fail "stack not healthy"

if $DOCKER_COMPOSE_BIN exec -T "$WORKER_SERVICE" celery \
  -A app.workers.celery_app.celery_app inspect ping --timeout=10 >> "$REPORT_FILE" 2>&1
then
  ok "celery worker ready"
else
  fail "celery worker not ready"
fi

if $DOCKER_COMPOSE_BIN exec -T "$API_SERVICE" python - <<'PY_SCHEMA' >> "$REPORT_FILE" 2>&1
import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import engine
Base.metadata.create_all(bind=engine)
print("OK schema bootstrap")
PY_SCHEMA
then
  ok "schema bootstrap guard"
else
  fail "schema bootstrap guard"
fi
$DOCKER_COMPOSE_BIN exec -T "$API_SERVICE" ffmpeg -version >> "$REPORT_FILE" 2>&1 || fail "ffmpeg missing in api"

if [[ "$AUTH_ENABLED" == "1" ]]; then
  login_body=$(printf '{"email":"%s","password":"%s"}' "$AUTH_EMAIL" "$AUTH_PASSWORD")
  if ! login_resp=$(curl -fsS -X POST "$BASE_URL/api/v1/auth/login" -H 'Content-Type: application/json' -d "$login_body" 2>>"$REPORT_FILE"); then
    fail "auth login request failed"
    login_resp=""
  fi
  token=$(printf '%s' "$login_resp" | json_get access_token)
  if [[ -n "$token" && "$token" != "null" ]]; then
    AUTH_ARGS=(-H "Authorization: Bearer $token")
    ok "auth login"
  else
    fail "auth login failed"
  fi
fi

if ! project_resp=$(curl -fsS -X POST "$BASE_URL/api/v1/projects" -H 'Content-Type: application/json' "${AUTH_ARGS[@]}" -d '{"title":"audio-e2e-test"}' 2>>"$REPORT_FILE"); then
  fail "project create request failed"
  project_resp=""
fi
PROJECT_ID=$(printf '%s' "$project_resp" | json_get id)
assert_not_empty "$PROJECT_ID" "project created"

if curl -fsS "$BASE_URL/api/v1/voices" -H 'Content-Type: application/json' "${AUTH_ARGS[@]}" >> "$REPORT_FILE" 2>&1; then
  ok "voices endpoint reachable"
else
  fail "voices endpoint unreachable"
fi

if [[ -n "$PROJECT_ID" && "$PROJECT_ID" != "null" ]]; then
  preview_body=$(printf '{"text":"preview test from ci","project_id":"%s"}' "$PROJECT_ID")
  if ! preview_resp=$(curl -fsS -X POST "$BASE_URL/api/v1/audio/preview" -H 'Content-Type: application/json' "${AUTH_ARGS[@]}" -d "$preview_body" 2>>"$REPORT_FILE"); then
    fail "preview create request failed"
    preview_resp=""
  fi
  PREVIEW_JOB_ID=$(printf '%s' "$preview_resp" | json_get id)
  assert_not_empty "$PREVIEW_JOB_ID" "preview job created"
else
  fail "skip preview: missing project_id"
fi

if [[ "$RUN_NARRATION_E2E" == "1" && -n "$PROJECT_ID" && "$PROJECT_ID" != "null" ]]; then
  narration_body=$(printf '{"project_id":"%s","text":"segment one. segment two. segment three."}' "$PROJECT_ID")
  if ! narration_resp=$(curl -fsS -X POST "$BASE_URL/api/v1/audio/narration" -H 'Content-Type: application/json' "${AUTH_ARGS[@]}" -d "$narration_body" 2>>"$REPORT_FILE"); then
    fail "narration create request failed"
    narration_resp=""
  fi
  NARRATION_JOB_ID=$(printf '%s' "$narration_resp" | json_get id)
  [[ -n "$NARRATION_JOB_ID" && "$NARRATION_JOB_ID" != "null" ]] && ok "narration job created $NARRATION_JOB_ID" || log "WARN: narration did not return job id"
fi

if [[ -n "$PREVIEW_JOB_ID" && "$PREVIEW_JOB_ID" != "null" ]]; then
  status=""
  job_resp=""
  for _ in $(seq 1 "$PREVIEW_POLL_ATTEMPTS"); do
    sleep 5
    job_resp=$(curl -fsS "$BASE_URL/api/v1/jobs/$PREVIEW_JOB_ID" "${AUTH_ARGS[@]}" 2>>"$REPORT_FILE" || true)
    printf '%s' "$job_resp" > "$PREVIEW_STATUS_FILE"
    status=$(printf '%s' "$job_resp" | json_get status)
    log "preview poll status=$status"
    if [[ "$status" == "succeeded" || "$status" == "completed" ]]; then
      ok "preview job succeeded"
      break
    fi
    if [[ "$status" == "failed" || "$status" == "error" ]]; then
      fail "preview job failed"
      break
    fi
  done
  if [[ "${status:-}" != "succeeded" && "${status:-}" != "completed" ]]; then
    log "last preview response:"
    cat "$PREVIEW_STATUS_FILE" >> "$REPORT_FILE" || true
    fail "preview job did not finish within timeout, last status=${status:-unknown}"
  else
    assert_job_artifacts "$(cat "$PREVIEW_STATUS_FILE")"
  fi
fi

if [[ "$RUN_NARRATION_E2E" == "1" && -n "$NARRATION_JOB_ID" && "$NARRATION_JOB_ID" != "null" ]]; then
  status=""
  for _ in $(seq 1 "$NARRATION_POLL_ATTEMPTS"); do
    sleep 5
    job_resp=$(curl -fsS "$BASE_URL/api/v1/jobs/$NARRATION_JOB_ID" "${AUTH_ARGS[@]}" 2>>"$REPORT_FILE" || true)
    printf '%s' "$job_resp" > "$NARRATION_STATUS_FILE"
    status=$(printf '%s' "$job_resp" | json_get status)
    log "narration poll status=$status"
    if [[ "$status" == "succeeded" || "$status" == "completed" ]]; then
      ok "narration job succeeded"
      assert_job_artifacts "$(cat "$NARRATION_STATUS_FILE")"
      break
    fi
    if [[ "$status" == "failed" || "$status" == "error" ]]; then
      fail "narration job failed"
      break
    fi
  done
  if [[ "${status:-}" != "succeeded" && "${status:-}" != "completed" ]]; then
    log "last narration response:"
    cat "$NARRATION_STATUS_FILE" >> "$REPORT_FILE" || true
    fail "narration job did not finish within timeout, last status=${status:-unknown}"
  fi
fi

$DOCKER_COMPOSE_BIN logs --tail=200 "$API_SERVICE" >> "$REPORT_FILE" 2>&1 || true
$DOCKER_COMPOSE_BIN logs --tail=200 "$WORKER_SERVICE" >> "$REPORT_FILE" 2>&1 || true

if [[ "$pass" == "true" ]]; then
  log "GO"
  exit 0
else
  log "NO-GO"
  exit 1
fi
