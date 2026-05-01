#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
REPORT="$ROOT/.verify_finevoice_audio_studio_patch.txt"
: > "$REPORT"

required_files=(
  "backend/app/core/provider_policy.py"
  "backend/app/services/audio_quality_gate.py"
  "backend/app/services/provider_capability_registry.py"
  "backend/app/api/system_capabilities.py"
  "backend/app/api/voice_design.py"
  "backend/app/api/voice_library.py"
  "backend/app/api/podcast.py"
)

for f in "${required_files[@]}"; do
  if [[ ! -f "$ROOT/$f" ]]; then
    echo "MISSING $f" | tee -a "$REPORT"
    exit 1
  fi
  echo "OK $f" >> "$REPORT"
done

if grep -R "silent wav\|placeholder" "$ROOT/backend/app" -n >> "$REPORT" 2>&1; then
  echo "WARN: placeholder references found. Ensure production policy blocks them." | tee -a "$REPORT"
fi

echo "FineVoice Audio Studio patch verification completed" | tee -a "$REPORT"
