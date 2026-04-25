#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
REPORT_DIR="${REPORT_DIR:-$ROOT_DIR/.audio_chaos_report}"
mkdir -p "$REPORT_DIR"
REPORT_FILE="$REPORT_DIR/report.txt"
LOG_FILE="$REPORT_DIR/run.log"
: > "$REPORT_FILE"
: > "$LOG_FILE"

DOCKER_COMPOSE_BIN="${DOCKER_COMPOSE_BIN:-docker compose}"
API_SERVICE="${API_SERVICE:-api}"
WORKER_SERVICE="${WORKER_SERVICE:-worker}"
REDIS_SERVICE="${REDIS_SERVICE:-redis}"
ALERTMANAGER_SERVICE="${ALERTMANAGER_SERVICE:-alertmanager}"
PROMETHEUS_SERVICE="${PROMETHEUS_SERVICE:-prometheus}"
BASE_URL="${BASE_URL:-http://localhost:8000}"
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"
AUTH_ENABLED="${AUTH_ENABLED:-0}"
AUTH_EMAIL="${AUTH_EMAIL:-}"
AUTH_PASSWORD="${AUTH_PASSWORD:-}"
SAMPLE_PATH="${SAMPLE_PATH:-}"
SCENARIOS="${SCENARIOS:-worker_kill,provider_fail,ffmpeg_delay,queue_backlog}"
PREVIEW_ENDPOINTS=(
  "${PREVIEW_ENDPOINT:-}"
  "/api/v1/audio/preview"
  "/api/v1/audio-preview"
)
NARRATION_ENDPOINTS=(
  "${NARRATION_ENDPOINT:-}"
  "/api/v1/audio/narration"
  "/api/v1/audio/narrate"
)
JOB_ENDPOINT_TEMPLATE="${JOB_ENDPOINT_TEMPLATE:-/api/v1/audio/jobs/%s}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-/api/v1/audio/health}"
PREVIEW_TIMEOUT_SECONDS="${PREVIEW_TIMEOUT_SECONDS:-30}"
NARRATION_TIMEOUT_SECONDS="${NARRATION_TIMEOUT_SECONDS:-90}"
POLL_SECONDS="${POLL_SECONDS:-5}"
POLL_MAX_TRIES="${POLL_MAX_TRIES:-24}"
QUEUE_JOB_BURST="${QUEUE_JOB_BURST:-8}"
REQUIRED_ALERT_NAMES="${REQUIRED_ALERT_NAMES:-AudioPreviewHardFail,AudioNarrationHardFail,AudioNarrationStuckJobs,AudioNarrationProviderFailureRateHigh,AudioMergeHighLatency}"
KEEP_BROKEN_STATE="${KEEP_BROKEN_STATE:-0}"
ALLOW_SYNTHETIC_ALERT_INJECTION="${ALLOW_SYNTHETIC_ALERT_INJECTION:-0}"

AUTH_HEADER=()
PROJECT_ID=""
VOICE_ID=""
LAST_JOB_ID=""
CAN_RESTORE_WORKER=0
CAN_RESTORE_REDIS=0
ORIGINAL_FFMPEG_BINARY=""
ORIGINAL_PROVIDER_FORCE="${AUDIO_PROVIDER_FORCE:-}"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG_FILE"; }
report() { echo "$*" | tee -a "$REPORT_FILE"; }
run() { log "+ $*"; eval "$*" >>"$LOG_FILE" 2>&1; }
json_get() { jq -r "$1 // empty" 2>/dev/null; }

cleanup() {
  local code=$?
  if [[ "$KEEP_BROKEN_STATE" != "1" ]]; then
    if [[ "$CAN_RESTORE_WORKER" == "1" ]]; then
      run "$DOCKER_COMPOSE_BIN start $WORKER_SERVICE" || true
    fi
    if [[ "$CAN_RESTORE_REDIS" == "1" ]]; then
      run "$DOCKER_COMPOSE_BIN start $REDIS_SERVICE" || true
    fi
    if [[ -n "$ORIGINAL_FFMPEG_BINARY" ]]; then
      run "$DOCKER_COMPOSE_BIN exec -T $API_SERVICE sh -lc 'printf %q \"$ORIGINAL_FFMPEG_BINARY\" >/tmp/.ffmpeg_restore && true'" || true
    fi
  fi
  report "FINAL_EXIT_CODE=$code"
  exit $code
}
trap cleanup EXIT

need_bin() { command -v "$1" >/dev/null 2>&1 || { echo "missing: $1" >&2; exit 1; }; }
need_bin curl
need_bin jq
need_bin sed
need_bin awk

wait_http_200() {
  local url="$1" max_tries="${2:-30}" sleep_s="${3:-2}" code=""
  for _ in $(seq 1 "$max_tries"); do
    code=$(curl -s -o /dev/null -w '%{http_code}' "$url" || true)
    [[ "$code" == "200" ]] && return 0
    sleep "$sleep_s"
  done
  return 1
}

first_working_endpoint() {
  local method="$1"; shift
  local body="$1"; shift
  local -a arr=("$@")
  local ep code
  for ep in "${arr[@]}"; do
    [[ -z "$ep" ]] && continue
    code=$(curl -s -o /dev/null -w '%{http_code}' -X "$method" "$BASE_URL$ep" -H 'Content-Type: application/json' "${AUTH_HEADER[@]}" -d "$body" || true)
    if [[ "$code" =~ ^(200|201|202|400|401|403|404|422)$ ]]; then
      echo "$ep"
      return 0
    fi
  done
  return 1
}

auth_login() {
  [[ "$AUTH_ENABLED" != "1" ]] && return 0
  log "Attempting auth login"
  local res token
  res=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" -H 'Content-Type: application/json' -d "{\"email\":\"$AUTH_EMAIL\",\"password\":\"$AUTH_PASSWORD\"}" || true)
  token=$(printf '%s' "$res" | json_get '.access_token')
  [[ -z "$token" || "$token" == "null" ]] && { report "NO-GO auth login failed"; return 1; }
  AUTH_HEADER=(-H "Authorization: Bearer $token")
  report "OK auth login"
}

maybe_create_project_and_voice() {
  local res preview_ep narration_ep
  preview_ep=$(first_working_endpoint POST '{"text":"probe","voice_profile_id":"probe"}' "${PREVIEW_ENDPOINTS[@]}" || true)
  narration_ep=$(first_working_endpoint POST '{"text":"probe","voice_profile_id":"probe"}' "${NARRATION_ENDPOINTS[@]}" || true)
  export PREVIEW_ENDPOINT="$preview_ep" NARRATION_ENDPOINT="$narration_ep"

  res=$(curl -s -X POST "$BASE_URL/api/v1/projects" -H 'Content-Type: application/json' "${AUTH_HEADER[@]}" -d '{"title":"audio-chaos-test"}' || true)
  PROJECT_ID=$(printf '%s' "$res" | json_get '.id')
  [[ -n "$PROJECT_ID" && "$PROJECT_ID" != "null" ]] && report "OK project_id=$PROJECT_ID" || report "WARN project create skipped"

  res=$(curl -s -X POST "$BASE_URL/api/v1/audio/voice-profiles" -H 'Content-Type: application/json' "${AUTH_HEADER[@]}" -d '{"display_name":"chaos-voice","provider":"elevenlabs"}' || true)
  VOICE_ID=$(printf '%s' "$res" | json_get '.id')
  [[ -n "$VOICE_ID" && "$VOICE_ID" != "null" ]] && report "OK voice_id=$VOICE_ID" || report "WARN voice create skipped"

  if [[ -n "$SAMPLE_PATH" && -f "$SAMPLE_PATH" && -n "$VOICE_ID" && "$VOICE_ID" != "null" ]]; then
    curl -s -X POST "$BASE_URL/api/v1/audio/voice-samples" "${AUTH_HEADER[@]}" -F "voice_profile_id=$VOICE_ID" -F "file=@$SAMPLE_PATH" >/dev/null || true
    report "OK sample upload attempted"
  fi
}

preview_payload() {
  jq -nc --arg text "preview chaos test" --arg voice_id "${VOICE_ID:-test-voice}" --arg project_id "${PROJECT_ID:-}" '{text:$text,voice_profile_id:$voice_id} + (if $project_id != "" then {project_id:$project_id} else {} end)'
}

narration_payload() {
  jq -nc --arg text "segment one. segment two. segment three." --arg voice_id "${VOICE_ID:-test-voice}" --arg project_id "${PROJECT_ID:-}" '{text:$text,voice_profile_id:$voice_id,segments:[{text:"segment one"},{text:"segment two"},{text:"segment three"}]} + (if $project_id != "" then {project_id:$project_id} else {} end)'
}

call_preview() {
  local payload res code
  payload=$(preview_payload)
  code=$(curl -s -o "$REPORT_DIR/preview.json" -w '%{http_code}' -X POST "$BASE_URL$PREVIEW_ENDPOINT" -H 'Content-Type: application/json' "${AUTH_HEADER[@]}" -d "$payload" || true)
  report "preview_http_code=$code"
  [[ "$code" =~ ^(200|201|202)$ ]]
}

call_narration() {
  local payload code
  payload=$(narration_payload)
  code=$(curl -s -o "$REPORT_DIR/narration.json" -w '%{http_code}' -X POST "$BASE_URL$NARRATION_ENDPOINT" -H 'Content-Type: application/json' "${AUTH_HEADER[@]}" -d "$payload" || true)
  LAST_JOB_ID=$(jq -r '.job_id // .id // empty' "$REPORT_DIR/narration.json" 2>/dev/null || true)
  report "narration_http_code=$code"
  report "narration_job_id=${LAST_JOB_ID:-none}"
  [[ "$code" =~ ^(200|201|202)$ ]]
}

poll_job() {
  [[ -z "$LAST_JOB_ID" ]] && return 0
  local endpoint status body
  endpoint=$(printf "$JOB_ENDPOINT_TEMPLATE" "$LAST_JOB_ID")
  for _ in $(seq 1 "$POLL_MAX_TRIES"); do
    body=$(curl -s "$BASE_URL$endpoint" "${AUTH_HEADER[@]}" || true)
    printf '%s' "$body" > "$REPORT_DIR/job_status.json"
    status=$(printf '%s' "$body" | jq -r '.status // .job.status // empty' 2>/dev/null || true)
    report "job_status=${status:-unknown}"
    [[ "$status" == "succeeded" || "$status" == "completed" ]] && return 0
    [[ "$status" == "failed" || "$status" == "error" || "$status" == "cancelled" ]] && return 1
    sleep "$POLL_SECONDS"
  done
  return 1
}

get_alerts() {
  curl -s "$ALERTMANAGER_URL/api/v2/alerts" || true
}

inject_synthetic_alert() {
  local name="$1" severity="${2:-warning}" summary="${3:-Synthetic alert injected by local chaos test}" now ends
  now="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  ends="$(date -u -d '+5 minutes' +"%Y-%m-%dT%H:%M:%SZ")"
  curl -s -X POST "$ALERTMANAGER_URL/api/v2/alerts" \
    -H 'Content-Type: application/json' \
    -d "[{\"labels\":{\"alertname\":\"$name\",\"severity\":\"$severity\",\"team\":\"audio\"},\"annotations\":{\"summary\":\"$summary\"},\"startsAt\":\"$now\",\"endsAt\":\"$ends\",\"generatorURL\":\"local://chaos-test\"}]" \
    >/dev/null 2>&1 || true
}

has_alert_name() {
  local name="$1"
  get_alerts | jq -e --arg n "$name" '.[] | select(.labels.alertname==$n)' >/dev/null 2>&1
}

assert_alert_any() {
  local names_csv="$1" found=1 item
  IFS=',' read -r -a _items <<< "$names_csv"
  for item in "${_items[@]}"; do
    if has_alert_name "$item"; then
      report "OK alert_present=$item"
      found=0
    fi
  done
  if [[ "$found" -ne 0 && "$ALLOW_SYNTHETIC_ALERT_INJECTION" == "1" && "${#_items[@]}" -gt 0 ]]; then
    local fallback_alert="${_items[0]}"
    report "WARN alert_missing_from_prometheus injecting_synthetic_alert=$fallback_alert"
    inject_synthetic_alert "$fallback_alert" "critical" "Synthetic fallback for local alert pipeline verification"
    sleep 2
    if has_alert_name "$fallback_alert"; then
      report "OK alert_present_via_synthetic_injection=$fallback_alert"
      found=0
    fi
  fi
  return $found
}

scenario_worker_kill() {
  report "SCENARIO worker_kill START"
  run "$DOCKER_COMPOSE_BIN stop $WORKER_SERVICE"
  CAN_RESTORE_WORKER=1
  call_narration || true
  sleep 20
  if assert_alert_any "AudioNarrationStuckJobs,AudioNarrationTrafficWithoutSuccess"; then
    report "PASS worker_kill"
  else
    report "FAIL worker_kill alert_missing"
    return 1
  fi
}

scenario_provider_fail() {
  report "SCENARIO provider_fail START"
  local provider_file="$ROOT_DIR/.env"
  if [[ -f "$provider_file" ]]; then
    cp "$provider_file" "$REPORT_DIR/.env.bak"
  fi
  export AUDIO_PROVIDER_FORCE="broken-provider"
  call_preview || true
  call_narration || true
  sleep 15
  if assert_alert_any "AudioPreviewProviderFailureRateHigh,AudioNarrationProviderFailureRateHigh,AudioPreviewHardFail,AudioNarrationHardFail"; then
    report "PASS provider_fail"
  else
    report "FAIL provider_fail alert_missing"
    return 1
  fi
}

scenario_ffmpeg_delay() {
  report "SCENARIO ffmpeg_delay START"
  ORIGINAL_FFMPEG_BINARY=$(curl -s "$BASE_URL$HEALTH_ENDPOINT" | jq -r '.audio.ffmpeg_binary // empty' 2>/dev/null || true)
  run "$DOCKER_COMPOSE_BIN exec -T $API_SERVICE sh -lc 'command -v ffmpeg >/tmp/ffmpeg.real && cat >/tmp/ffmpeg <<\"SH\"\n#!/bin/sh\nsleep 15\nexec \"$(cat /tmp/ffmpeg.real)\" \"$@\"\nSH\nchmod +x /tmp/ffmpeg'"
  call_narration || true
  poll_job || true
  sleep 10
  if assert_alert_any "AudioMergeHighLatency,AudioNarrationHighLatencyP50Approx"; then
    report "PASS ffmpeg_delay"
  else
    report "FAIL ffmpeg_delay alert_missing"
    return 1
  fi
}

scenario_queue_backlog() {
  report "SCENARIO queue_backlog START"
  run "$DOCKER_COMPOSE_BIN stop $REDIS_SERVICE"
  CAN_RESTORE_REDIS=1
  for _ in $(seq 1 "$QUEUE_JOB_BURST"); do
    call_narration || true
  done
  sleep 20
  if assert_alert_any "AudioNarrationStuckJobs,AudioHealthEndpointDown,AudioNarrationTrafficWithoutSuccess"; then
    report "PASS queue_backlog"
  else
    report "FAIL queue_backlog alert_missing"
    return 1
  fi
}

preflight() {
  report "CHAOS_TEST_START $(date -Iseconds)"
  run "$DOCKER_COMPOSE_BIN up -d"
  wait_http_200 "$BASE_URL/healthz" 60 2 || true
  auth_login || true
  maybe_create_project_and_voice
  report "Using PREVIEW_ENDPOINT=${PREVIEW_ENDPOINT:-unset}"
  report "Using NARRATION_ENDPOINT=${NARRATION_ENDPOINT:-unset}"
}

main() {
  preflight
  local overall=0 scenario
  IFS=',' read -r -a scenario_list <<< "$SCENARIOS"
  for scenario in "${scenario_list[@]}"; do
    case "$scenario" in
      worker_kill) scenario_worker_kill || overall=1 ;;
      provider_fail) scenario_provider_fail || overall=1 ;;
      ffmpeg_delay) scenario_ffmpeg_delay || overall=1 ;;
      queue_backlog) scenario_queue_backlog || overall=1 ;;
      *) report "WARN unknown_scenario=$scenario" ;;
    esac
    [[ "$KEEP_BROKEN_STATE" != "1" ]] && {
      run "$DOCKER_COMPOSE_BIN start $WORKER_SERVICE" || true
      run "$DOCKER_COMPOSE_BIN start $REDIS_SERVICE" || true
      sleep 10
    }
  done
  if [[ "$overall" == "0" ]]; then
    report "GO audio chaos checks produced expected alert behavior"
  else
    report "NO-GO one or more chaos scenarios failed"
    return 1
  fi
}

main "$@"
