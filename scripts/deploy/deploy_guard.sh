#!/usr/bin/env bash
set -Eeuo pipefail

REPORT_DIR="${REPORT_DIR:-.deploy_guard}"
mkdir -p "$REPORT_DIR"
REPORT="$REPORT_DIR/report.txt"
STATE_FILE="$REPORT_DIR/state.env"

log(){ printf '%s %s\n' "[$(date '+%Y-%m-%d %H:%M:%S')]" "$*" | tee -a "$REPORT"; }
fail(){ log "NO-GO: $*"; exit 1; }

: > "$REPORT"
log "Starting deploy guard"
log "DEPLOY_ENV=${DEPLOY_ENV:-} DEPLOY_REF=${DEPLOY_REF:-} RELEASE_ID=${RELEASE_ID:-}"

CURRENT_REVISION="${CURRENT_REVISION:-${DEPLOY_REF:-unknown}}"
PREVIOUS_REVISION="${PREVIOUS_REVISION:-}"

echo "CURRENT_REVISION=$CURRENT_REVISION" > "$STATE_FILE"
echo "PREVIOUS_REVISION=$PREVIOUS_REVISION" >> "$STATE_FILE"
echo "DEPLOY_ENV=${DEPLOY_ENV:-}" >> "$STATE_FILE"
echo "RELEASE_ID=${RELEASE_ID:-}" >> "$STATE_FILE"

if [[ -z "${DEPLOY_COMMAND:-}" ]]; then
  fail "DEPLOY_COMMAND is not set"
fi

log "Running deploy command"
if ! bash -lc "$DEPLOY_COMMAND" >> "$REPORT" 2>&1; then
  fail "deploy command failed before post-deploy smoke"
fi

log "Running post-deploy audio smoke"
chmod +x scripts/deploy/post_deploy_audio_smoke.sh || true
if ! bash scripts/deploy/post_deploy_audio_smoke.sh >> "$REPORT" 2>&1; then
  log "Post-deploy audio smoke failed; starting auto rollback"
  chmod +x scripts/deploy/auto_rollback.sh || true
  if bash scripts/deploy/auto_rollback.sh >> "$REPORT" 2>&1; then
    log "ROLLBACK_OK"
    exit 1
  else
    fail "rollback failed after audio smoke failure"
  fi
fi

log "GO: deploy guard passed"
