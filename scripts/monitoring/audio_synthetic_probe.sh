#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
AUTH_ENABLED="${AUTH_ENABLED:-0}"
AUTH_EMAIL="${AUTH_EMAIL:-}"
AUTH_PASSWORD="${AUTH_PASSWORD:-}"
SAMPLE_TEXT="${AUDIO_SYNTHETIC_SAMPLE_TEXT:-This is a synthetic preview check for the audio platform.}"
TIMEOUT_SECONDS="${AUDIO_HEALTH_CHECK_TIMEOUT_SECONDS:-30}"
REPORT_DIR="${REPORT_DIR:-.audio_synthetic_probe}"
mkdir -p "$REPORT_DIR"

AUTH_HEADERS=()
if [[ "$AUTH_ENABLED" == "1" ]]; then
  LOGIN_PAYLOAD=$(python3 - <<PY
import json
print(json.dumps({"email": "${AUTH_EMAIL}", "password": "${AUTH_PASSWORD}"}))
PY
)
  TOKEN=$(curl -sS -X POST "$BASE_URL/api/v1/auth/login" -H 'Content-Type: application/json' -d "$LOGIN_PAYLOAD" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("access_token",""))' || true)
  if [[ -z "$TOKEN" ]]; then
    echo "WARN: auth enabled but token unavailable, continue without auth" | tee "$REPORT_DIR/auth.warn"
  else
    AUTH_HEADERS=(-H "Authorization: Bearer $TOKEN")
  fi
fi

STATUS=$(curl -sS -m "$TIMEOUT_SECONDS" -o "$REPORT_DIR/health.json" -w '%{http_code}' "$BASE_URL/api/v1/audio/health" "${AUTH_HEADERS[@]}" || true)
[[ "$STATUS" != "200" ]] && echo "NO-GO: audio health endpoint returned $STATUS" && exit 1

PREVIEW_PAYLOAD=$(python3 - <<PY
import json
print(json.dumps({"text": "${SAMPLE_TEXT}", "voice_profile_id": "synthetic-default"}))
PY
)

PREVIEW_HTTP=$(curl -sS -m "$TIMEOUT_SECONDS" -o "$REPORT_DIR/preview.json" -w '%{http_code}' -X POST "$BASE_URL/api/v1/audio/preview" -H 'Content-Type: application/json' "${AUTH_HEADERS[@]}" -d "$PREVIEW_PAYLOAD" || true)
if [[ "$PREVIEW_HTTP" != "200" && "$PREVIEW_HTTP" != "201" ]]; then
  echo "NO-GO: preview probe failed with $PREVIEW_HTTP" | tee "$REPORT_DIR/status.txt"
  exit 1
fi

NARRATION_PAYLOAD=$(python3 - <<PY
import json
print(json.dumps({"text": "${SAMPLE_TEXT}", "voice_profile_id": "synthetic-default"}))
PY
)
NARRATION_HTTP=$(curl -sS -m "$TIMEOUT_SECONDS" -o "$REPORT_DIR/narration.json" -w '%{http_code}' -X POST "$BASE_URL/api/v1/audio/narration" -H 'Content-Type: application/json' "${AUTH_HEADERS[@]}" -d "$NARRATION_PAYLOAD" || true)
if [[ "$NARRATION_HTTP" != "200" && "$NARRATION_HTTP" != "201" && "$NARRATION_HTTP" != "202" ]]; then
  echo "NO-GO: narration probe failed with $NARRATION_HTTP" | tee "$REPORT_DIR/status.txt"
  exit 1
fi

echo "GO: preview and narration synthetic probes succeeded" | tee "$REPORT_DIR/status.txt"
