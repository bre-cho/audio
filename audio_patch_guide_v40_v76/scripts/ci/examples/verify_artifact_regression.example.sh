#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

API_BASE="${API_BASE:-http://localhost:8000/api/v1}"
REPORT_FILE="${REPORT_FILE:-reports/artifact_regression_report.txt}"
mkdir -p "$(dirname "$REPORT_FILE")"
: > "$REPORT_FILE"

fail() { echo "[FAIL] $1" | tee -a "$REPORT_FILE"; exit 1; }
ok() { echo "[OK] $1" | tee -a "$REPORT_FILE"; }

json_get() {
  python -c 'import json,sys; data=json.loads(sys.argv[1]); print(data.get(sys.argv[2], ""))' "$1" "$2"
}

run_replay_regression() {
  local artifact_id="$1"

  response="$(curl -sf -X POST "$API_BASE/artifacts/$artifact_id/replay?dry_run=true")" \
    || fail "replay dry-run failed: $artifact_id"

  regression_status="$(json_get "$response" "regression_status")"
  drift_status="$(json_get "$response" "drift_status")"

  [[ "$regression_status" == "pass" ]] || fail "regression failed: $artifact_id"
  [[ "$drift_status" == "none" || "$drift_status" == "within_budget" ]] \
    || fail "drift exceeded budget: $artifact_id"

  ok "artifact regression stable: $artifact_id"
}

for artifact_id in "$@"; do
  run_replay_regression "$artifact_id"
done

ok "artifact regression completed"
