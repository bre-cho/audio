#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

REPORT_FILE="${REPORT_FILE:-reports/verify_audio_patch_report.txt}"
mkdir -p "$(dirname "$REPORT_FILE")"
: > "$REPORT_FILE"

fail() {
  echo "[FAIL] $1" | tee -a "$REPORT_FILE"
  exit 1
}

ok() {
  echo "[OK] $1" | tee -a "$REPORT_FILE"
}

trap 'echo "[FATAL] Script failed at line $LINENO" >> "$REPORT_FILE"' ERR

run() {
  local desc="$1"
  shift
  if ! "$@" >> "$REPORT_FILE" 2>&1; then
    fail "$desc"
  fi
  ok "$desc"
}

SEARCH_PATHS=(backend/app/api)
if [[ -d backend/app/services/audio ]]; then
  SEARCH_PATHS+=(backend/app/services/audio)
fi

if grep -R "ElevenLabsAdapter()" "${SEARCH_PATHS[@]}" -n >> "$REPORT_FILE" 2>&1; then
  fail "hardcoded ElevenLabsAdapter still present"
else
  ok "no hardcoded ElevenLabsAdapter in audio route/service"
fi

if [[ -d backend/app/services/audio ]]; then
  grep -R "combined_audio += audio_bytes" backend/app/services/audio -n >> "$REPORT_FILE" 2>&1 || true
  ok "combined audio grep completed"
fi

[[ -s "$REPORT_FILE" ]] || fail "report file is empty"
ok "verify_audio_patch completed"
