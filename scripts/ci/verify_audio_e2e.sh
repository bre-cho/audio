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
VOICE_ID=""
PREVIEW_URL=""
NARRATION_JOB_ID=""
FINAL_OUTPUT_URL=""
FINAL_FILE="$REPORT_DIR/final_audio.bin"

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

voice_resp=$(curl -fsS -X POST "$BASE_URL/api/v1/audio/voice-profiles" -H 'Content-Type: application/json' "${AUTH_ARGS[@]}" -d '{"display_name":"e2e-voice","provider":"elevenlabs"}' 2>>"$REPORT_FILE" || true)
VOICE_ID=$(printf '%s' "$voice_resp" | json_get id)
[[ -n "$VOICE_ID" && "$VOICE_ID" != "null" ]] && log "OK: voice profile created $VOICE_ID" || fail "voice profile create failed"

if [[ -f "$SAMPLE_PATH" ]]; then
  curl -fsS -X POST "$BASE_URL/api/v1/audio/voice-samples" "${AUTH_ARGS[@]}" -F "voice_profile_id=$VOICE_ID" -F "file=@$SAMPLE_PATH" >> "$REPORT_FILE" 2>&1 || fail "voice sample upload failed"
else
  log "WARN: sample file not found, skipping upload"
fi

preview_body=$(printf '{"text":"preview test from ci","voice_profile_id":"%s","project_id":"%s"}' "$VOICE_ID" "$PROJECT_ID")
preview_resp=$(curl -fsS -X POST "$BASE_URL/api/v1/audio/preview" -H 'Content-Type: application/json' "${AUTH_ARGS[@]}" -d "$preview_body" 2>>"$REPORT_FILE" || true)
PREVIEW_URL=$(printf '%s' "$preview_resp" | json_get preview_url)
[[ -n "$PREVIEW_URL" && "$PREVIEW_URL" != "null" ]] && log "OK: preview url returned" || fail "preview url missing"

narration_body=$(printf '{"project_id":"%s","text":"segment one. segment two. segment three.","voice_profile_id":"%s"}' "$PROJECT_ID" "$VOICE_ID")
narration_resp=$(curl -fsS -X POST "$BASE_URL/api/v1/audio/narration" -H 'Content-Type: application/json' "${AUTH_ARGS[@]}" -d "$narration_body" 2>>"$REPORT_FILE" || true)
NARRATION_JOB_ID=$(printf '%s' "$narration_resp" | json_get id)
FINAL_OUTPUT_URL=$(printf '%s' "$narration_resp" | json_get output_url)
[[ -n "$NARRATION_JOB_ID" && "$NARRATION_JOB_ID" != "null" ]] && log "OK: narration job created $NARRATION_JOB_ID" || log "WARN: narration did not return job id"

if [[ -n "$NARRATION_JOB_ID" && "$NARRATION_JOB_ID" != "null" ]]; then
  for _ in {1..40}; do
    sleep 5
    job_resp=$(curl -fsS "$BASE_URL/api/v1/audio/narration/$NARRATION_JOB_ID" "${AUTH_ARGS[@]}" 2>>"$REPORT_FILE" || true)
    status=$(printf '%s' "$job_resp" | json_get status)
    FINAL_OUTPUT_URL=$(printf '%s' "$job_resp" | json_get output_url)
    log "poll status=$status"
    if [[ "$status" == "succeeded" || "$status" == "completed" ]]; then
      break
    fi
    if [[ "$status" == "failed" || "$status" == "error" ]]; then
      fail "narration job failed"
      break
    fi
  done
fi

if [[ -n "$FINAL_OUTPUT_URL" && "$FINAL_OUTPUT_URL" != "null" ]]; then
  curl -fsS "$FINAL_OUTPUT_URL" -o "$FINAL_FILE" 2>>"$REPORT_FILE" || fail "download final audio failed"
  if [[ -f "$FINAL_FILE" ]]; then
    ffprobe -v error -show_format -show_streams "$FINAL_FILE" >> "$REPORT_FILE" 2>&1 || fail "ffprobe could not read final audio"
  else
    fail "final audio file missing"
  fi
else
  fail "final output url missing"
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
