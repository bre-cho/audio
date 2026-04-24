#!/usr/bin/env bash
set -Eeuo pipefail

REPORT_DIR="${REPORT_DIR:-.deploy_guard}"
STATE_FILE="$REPORT_DIR/state.env"
[[ -f "$STATE_FILE" ]] && source "$STATE_FILE"

log(){ printf '%s %s\n' "[$(date '+%Y-%m-%d %H:%M:%S')]" "$*"; }

if [[ -n "${ROLLBACK_COMMAND:-}" ]]; then
  log "Running explicit rollback command"
  bash -lc "$ROLLBACK_COMMAND"
  exit 0
fi

if [[ -z "${PREVIOUS_REVISION:-}" ]]; then
  log "No PREVIOUS_REVISION and no ROLLBACK_COMMAND; cannot rollback"
  exit 1
fi

log "Rolling back to PREVIOUS_REVISION=$PREVIOUS_REVISION"
if [[ -x ./scripts/deploy/deploy.sh ]]; then
  DEPLOY_REF="$PREVIOUS_REVISION" bash ./scripts/deploy/deploy.sh
else
  log "Fallback rollback: git checkout $PREVIOUS_REVISION"
  git checkout "$PREVIOUS_REVISION"
fi
