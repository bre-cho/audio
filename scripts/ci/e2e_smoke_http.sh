#!/usr/bin/env bash
# ============================================================
# FineVoice Audio Studio – HTTP E2E Smoke Script
# Usage: bash scripts/ci/e2e_smoke_http.sh [API_BASE] [FRONTEND_BASE]
# Defaults: API_BASE=http://localhost:8000  FRONTEND_BASE=http://localhost:3000
# Exit code 0 = all checks passed, non-zero = at least one failure.
# ============================================================
set -euo pipefail

API="${1:-http://localhost:8000}"
FE="${2:-http://localhost:3000}"
PASS=0
FAIL=0

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

check() {
  local label="$1" expected="$2"
  shift 2
  local actual
  actual=$(curl -sS -o /tmp/_e2e_body.txt -w '%{http_code}' "$@")
  local body
  body=$(cat /tmp/_e2e_body.txt)
  if [[ "$actual" == "$expected" ]]; then
    echo -e "${GREEN}PASS${NC} [$label] HTTP $actual"
    PASS=$((PASS+1))
  else
    echo -e "${RED}FAIL${NC} [$label] expected HTTP $expected, got HTTP $actual"
    echo "       body: ${body:0:200}"
    FAIL=$((FAIL+1))
  fi
}

# ------------------------------------------------------------------
# Generate a minimal WAV base64 for podcast/mix payload
# ------------------------------------------------------------------
WAV_B64=$(python3 - <<'PY'
import base64, io, wave, struct, math
def make_wav(dur_ms, freq=440, rate=16000):
    buf = io.BytesIO()
    n = int(rate * dur_ms / 1000)
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(rate)
        wf.writeframes(struct.pack('<'+str(n)+'h', *[
            int(32000*math.sin(2*math.pi*freq*i/rate)) for i in range(n)
        ]))
    return base64.b64encode(buf.getvalue()).decode()
print(make_wav(500))
PY
)

PODCAST_PAYLOAD=$(python3 -c "
import json, sys
b = sys.argv[1]
print(json.dumps({'title':'E2E Episode','segments':[
  {'audio_b64':b,'speaker':'Host','pause_after_ms':200},
  {'audio_b64':b,'speaker':'Guest','pause_after_ms':0}
]}))" "$WAV_B64")

# ------------------------------------------------------------------
# Infrastructure
# ------------------------------------------------------------------
echo ""
echo "== Infrastructure =="
check "healthz"                         200 "$API/healthz"
check "frontend-index"                  200 "$FE/"

# ------------------------------------------------------------------
# P0 – System Capabilities
# ------------------------------------------------------------------
echo ""
echo "== P0 System Capabilities =="
check "system/capabilities (direct)"   200 "$API/api/v1/system/capabilities"
check "system/capabilities (via FE)"   200 "$FE/api/v1/system/capabilities"
check "route-no-double-api (404 guard)" 404 "$API/api/v1/api/system/capabilities"

# ------------------------------------------------------------------
# P1 – Voice Library & Voice Design
# ------------------------------------------------------------------
echo ""
echo "== P1 Voice Library / Design =="
check "voice-library/voices GET"       200 "$API/api/v1/voice-library/voices"
check "voice-design/recipes GET"       200 "$API/api/v1/voice-design/recipes"
check "voice-design/recipes POST" 200 \
  -X POST "$API/api/v1/voice-design/recipes" \
  -H 'Content-Type: application/json' \
  -d '{"name":"e2e-recipe","style":"warm","emotion":"calm","language":"vi"}'

# ------------------------------------------------------------------
# P4 – BGM (capability-gate: blocked → 409 expected)
# ------------------------------------------------------------------
echo ""
echo "== P4 BGM (capability-blocked gate) =="
check "bgm/generate 409-blocked"       409 \
  -X POST "$API/api/v1/bgm/generate" \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"test","duration_sec":30}'

# ------------------------------------------------------------------
# P5 – Podcast status + mix
# ------------------------------------------------------------------
echo ""
echo "== P5 Podcast =="
check "podcast/status"                 200 "$API/api/v1/podcast/status"
check "podcast/mix 200 with real WAV" 200 \
  -X POST "$API/api/v1/podcast/mix" \
  -H 'Content-Type: application/json' \
  -d "$PODCAST_PAYLOAD"
check "podcast/mix 400 no audio_b64"  400 \
  -X POST "$API/api/v1/podcast/mix" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Bad","segments":[{"speaker":"X","pause_after_ms":0}]}'

# ------------------------------------------------------------------
# P6 – STT/Transcription & Localization (capability-gate)
# ------------------------------------------------------------------
echo ""
echo "== P6 Transcription / Localization (capability-blocked gate) =="
check "transcription/transcribe 409"  409 \
  -X POST "$API/api/v1/transcription/transcribe" \
  -H 'Content-Type: application/json' \
  -d '{"artifact_id":"art_test","language":"vi","export_formats":["json"]}'
check "localization/voice-translate 409" 409 \
  -X POST "$API/api/v1/localization/voice-translate" \
  -H 'Content-Type: application/json' \
  -d '{"source_artifact_id":"art_test","target_language":"en","preserve_voice":true}'

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
echo ""
echo "========================================"
echo -e "Results: ${GREEN}${PASS} passed${NC} / ${RED}${FAIL} failed${NC}"
echo "========================================"
[[ $FAIL -eq 0 ]]
