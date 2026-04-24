#!/usr/bin/env bash
# audio_slack_dedupe_guard.sh
# Exports incident state variables for downstream deduplication and reporting.

set -euo pipefail

# v17 — finalizer status
FINALIZER_STATUS="$(python - <<'PY'
import json
try:
    with open(".incident_classification.json") as f:
        print(json.load(f).get("finalizer", {}).get("status", "not_finalized"))
except Exception:
    print("not_finalized")
PY
)"

# v17 — postmortem seed path
POSTMORTEM_SEED="$(python - <<'PY'
import json
try:
    with open(".incident_classification.json") as f:
        print(json.load(f).get("finalizer", {}).get("postmortem_seed", ""))
except Exception:
    print("")
PY
)"

# v18 — knowledge fingerprint
KM_FP="$(python - <<'PY'
import json
try:
    with open(".incident_classification.json") as f:
        print(json.load(f).get("knowledge_memory", {}).get("fingerprint", ""))
except Exception:
    print("")
PY
)"

# v18 — knowledge pattern count
KM_COUNT="$(python - <<'PY'
import json
try:
    with open(".incident_classification.json") as f:
        print(json.load(f).get("knowledge_memory", {}).get("pattern_count", 0))
except Exception:
    print(0)
PY
)"

export FINALIZER_STATUS POSTMORTEM_SEED KM_FP KM_COUNT
