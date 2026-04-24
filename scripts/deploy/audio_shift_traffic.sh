#!/usr/bin/env bash
set -euo pipefail

STEPS=${1:-5,25,50,100}
mkdir -p .audio_canary

echo "$STEPS" | tr ',' '\n' | while read -r PCT; do
  [[ -z "$PCT" ]] && continue
  echo "[audio-canary] shifting traffic to ${PCT}% canary" | tee -a .audio_canary/traffic_shift.log
  export CANARY_PERCENT="$PCT"
  bash -lc "$SHIFT_TRAFFIC_COMMAND" | tee -a .audio_canary/traffic_shift.log
  bash scripts/deploy/post_canary_audio_smoke.sh step "$PCT"
done
