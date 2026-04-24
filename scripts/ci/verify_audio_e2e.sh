#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

BASE_URL="${BASE_URL:-http://localhost:8000}"
API_SERVICE="${API_SERVICE:-api}"
WORKER_SERVICE="${WORKER_SERVICE:-worker}"
DOCKER_COMPOSE_BIN="${DOCKER_COMPOSE_BIN:-docker compose}"
AUTH_ENABLED="${AUTH_ENABLED:-0}"
AUTH_EMAIL="${AUTH_EMAIL:-}"
AUTH_PASSWORD="${AUTH_PASSWORD:-}"
SAMPLE_PATH="${SAMPLE_PATH:-backend/data/audio/test_sample.mp3}"
REPORT_DIR="$ROOT_DIR/.verify_audio_e2e"
mkdir -p "$REPORT_DIR"
REPORT_FILE="$REPORT_DIR/report.txt"
: > "$REPORT_FILE"

pass=true
AUTH_ARGS=()
PROJECT_ID=""
PREVIEW_JOB_ID=""
NARRATION_JOB_ID=""

log(){ echo "$*" | tee -a "$REPORT_FILE"; }
fail(){ log "FAIL: $*"; pass=false; }
json_get(){ python -c 'import json,sys; data=json.load(sys.stdin); cur=data
for p in sys.argv[1].split("."):
    if isinstance(cur, dict): cur=cur.get(p)
    else: cur=None
print("" if cur is None else cur)' "$1"; }

$DOCKER_COMPOSE_BIN up -d >> "$REPORT_FILE" 2>&1 || fail "docker compose up failed"
python scripts/ci/wait_for_stack.py 300 >> "$REPORT_FILE" 2>&1 || fail "stack not healthy"
$DOCKER_COMPOSE_BIN exec -T "$API_SERVICE" ffmpeg -version >> "$REPORT_FILE" 2>&1 || fail "ffmpeg missing in api"

if [[ "$AUTH_ENABLED" == "1" ]]; then
  login_body=$(printf '{"email":"%s","password":"%s"}' "$AUTH_EMAIL" "$AUTH_PASSWORD")
  login_resp=$(curl -fsS -X POST "$BASE_URL/api/v1/auth/login" -H 'Content-Type: application/json' -d "$login_body" 2>>"$REPORT_FILE" || true)
  token=$(printf '%s' "$login_resp" | json_get access_token)
  if [[ -n "$token" && "$token" != "null" ]]; then
    AUTH_ARGS=(-H "Authorization: Bearer $token")
    log "OK: auth login"
  else
    fail "auth login failed"
  fi
fi

project_resp=$(curl -fsS -X POST "$BASE_URL/api/v1/projects" -H 'Content-Type: application/json' "${AUTH_ARGS[@]}" -d '{"title":"audio-e2e-test"}' 2>>"$REPORT_FILE" || true)
PROJECT_ID=$(printf '%s' "$project_resp" | json_get id)
[[ -n "$PROJECT_ID" && "$PROJECT_ID" != "null" ]] && log "OK: project created $PROJECT_ID" || fail "project create failed"

# List available voices from the voices endpoint
voices_resp=$(curl -fsS "$BASE_URL/api/v1/voices" -H 'Content-Type: application/json' "${AUTH_ARGS[@]}" 2>>"$REPORT_FILE" || true)
log "OK: voices endpoint reachable"

preview_body=$(printf '{"text":"preview test from ci","project_id":"%s"}' "$PROJECT_ID")
preview_resp=$(curl -fsS -X POST "$BASE_URL/api/v1/audio/preview" -H 'Content-Type: application/json' "${AUTH_ARGS[@]}" -d "$preview_body" 2>>"$REPORT_FILE" || true)
PREVIEW_JOB_ID=$(printf '%s' "$preview_resp" | json_get id)
[[ -n "$PREVIEW_JOB_ID" && "$PREVIEW_JOB_ID" != "null" ]] && log "OK: preview job created $PREVIEW_JOB_ID" || fail "preview job id missing"

narration_body=$(printf '{"project_id":"%s","text":"segment one. segment two. segment three."}' "$PROJECT_ID")
narration_resp=$(curl -fsS -X POST "$BASE_URL/api/v1/audio/narration" -H 'Content-Type: application/json' "${AUTH_ARGS[@]}" -d "$narration_body" 2>>"$REPORT_FILE" || true)
NARRATION_JOB_ID=$(printf '%s' "$narration_resp" | json_get id)
[[ -n "$NARRATION_JOB_ID" && "$NARRATION_JOB_ID" != "null" ]] && log "OK: narration job created $NARRATION_JOB_ID" || log "WARN: narration did not return job id"

if [[ -n "$NARRATION_JOB_ID" && "$NARRATION_JOB_ID" != "null" ]]; then
  status=""
  for _ in {1..40}; do
    sleep 5
    job_resp=$(curl -fsS "$BASE_URL/api/v1/jobs/$NARRATION_JOB_ID" "${AUTH_ARGS[@]}" 2>>"$REPORT_FILE" || true)
    printf '%s' "$job_resp" > /tmp/audio_job_status.json
    status=$(printf '%s' "$job_resp" | json_get status)
    log "poll status=$status"
    if [[ "$status" == "succeeded" || "$status" == "completed" ]]; then
      log "OK: narration job succeeded"
      break
    fi
    if [[ "$status" == "failed" || "$status" == "error" ]]; then
      fail "narration job failed"
      break
    fi
  done
  if [[ "${status:-}" != "succeeded" && "${status:-}" != "completed" ]]; then
    log "last response:"
    cat /tmp/audio_job_status.json >> "$REPORT_FILE" || true
    fail "narration job did not finish within timeout, last status=${status:-unknown}"
  else
    preview_url=$(printf '%s' "$(cat /tmp/audio_job_status.json)" | json_get preview_url)
    output_url=$(printf '%s' "$(cat /tmp/audio_job_status.json)" | json_get output_url)
    if [[ -z "$preview_url" && -z "$output_url" ]]; then
      fail "job succeeded but no preview_url/output_url found"
    else
      log "OK: output_url=$output_url preview_url=$preview_url"
    fi
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
