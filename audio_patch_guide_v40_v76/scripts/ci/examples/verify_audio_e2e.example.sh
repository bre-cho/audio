#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

API_BASE="${API_BASE:-http://localhost:8000/api/v1}"
REPORT_FILE="${REPORT_FILE:-reports/verify_audio_e2e_report.txt}"
REPORT_DIR="${REPORT_DIR:-reports/e2e}"
mkdir -p "$(dirname "$REPORT_FILE")" "$REPORT_DIR"
: > "$REPORT_FILE"

fail() { echo "[FAIL] $1" | tee -a "$REPORT_FILE"; exit 1; }
ok() { echo "[OK] $1" | tee -a "$REPORT_FILE"; }
log() { echo "[LOG] $1" | tee -a "$REPORT_FILE"; }

trap 'echo "[FATAL] Script failed at line $LINENO" >> "$REPORT_FILE"' ERR

json_get() {
  python -c 'import json,sys; data=json.loads(sys.argv[1]); print(data.get(sys.argv[2], ""))' "$1" "$2"
}

assert_not_empty() {
  local value="$1"
  local msg="$2"
  [[ -n "$value" && "$value" != "null" ]] || fail "$msg"
  ok "$msg"
}

assert_json_key() {
  local json="$1"
  local key="$2"
  local value
  value="$(json_get "$json" "$key")"
  assert_not_empty "$value" "json key exists: $key"
}

assert_file_exists() {
  local path="$1"
  [[ -f "$path" ]] || fail "missing file: $path"
  ok "file exists: $path"
}

project_body='{"name":"ci audio e2e project"}'
project_response="$(curl -sf -X POST "$API_BASE/projects" -H 'Content-Type: application/json' -d "$project_body")" \
  || fail "project create request failed"

assert_json_key "$project_response" "id"
PROJECT_ID="$(json_get "$project_response" "id")"
assert_not_empty "$PROJECT_ID" "project_id created"

preview_body=$(printf '{"text":"preview test from ci","project_id":"%s"}' "$PROJECT_ID")
preview_response="$(curl -sf -X POST "$API_BASE/audio/preview" -H 'Content-Type: application/json' -d "$preview_body")" \
  || fail "preview request failed"

assert_json_key "$preview_response" "id"
assert_json_key "$preview_response" "status"

[[ -s "$REPORT_FILE" ]] || fail "report file is empty"
ok "verify_audio_e2e completed"
