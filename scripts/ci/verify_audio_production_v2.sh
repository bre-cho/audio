#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

fail() { echo "[FAIL] $*" >&2; exit 1; }
pass() { echo "[PASS] $*"; }

python - <<'PY'
import os
required = [
  'backend/app/core/production_truth.py',
  'backend/app/services/provider_capability_gate_v2.py',
  'backend/app/services/audio_signal_validator.py',
]
missing = [p for p in required if not os.path.exists(p)]
if missing:
    raise SystemExit('missing required files: ' + ', '.join(missing))
print('[PASS] required patch files exist')
PY

if [ -f backend/pytest.ini ] || [ -d backend/tests ]; then
  (cd backend && pytest -q tests/test_p0_runtime_truth.py tests/test_p1_provider_capability_gate.py) || fail "pytest failed"
  pass "pytest runtime/capability tests passed"
fi

if grep -R "allow_placeholder_audio.*True" backend/app/core/config.py >/dev/null 2>&1; then
  fail "config.py still defaults allow_placeholder_audio to True"
else
  pass "placeholder default guard appears safe or not found"
fi

pass "audio production v2 verification completed"
