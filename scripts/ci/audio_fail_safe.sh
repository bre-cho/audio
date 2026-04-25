#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

API_SERVICE="${API_SERVICE:-api}"
WORKER_SERVICE="${WORKER_SERVICE:-worker}"
DOCKER_COMPOSE_BIN="${DOCKER_COMPOSE_BIN:-}"
OUT_DIR="artifacts/audio-ci"
mkdir -p "$OUT_DIR"

resolve_compose_cmd() {
  if [[ -n "$DOCKER_COMPOSE_BIN" ]]; then
    # shellcheck disable=SC2206
    COMPOSE_CMD=($DOCKER_COMPOSE_BIN)
    return
  fi
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
    return
  fi
  if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
    return
  fi
  echo "WARNING: docker compose not found; skipping container log collection" >&2
  COMPOSE_CMD=()
}

dc() {
  if [[ "${#COMPOSE_CMD[@]}" -eq 0 ]]; then return 0; fi
  "${COMPOSE_CMD[@]}" "$@"
}

resolve_compose_cmd

dc ps -a > "$OUT_DIR/docker-compose-ps.txt" 2>&1 || true
dc logs --no-color --tail=400 "$API_SERVICE" > "$OUT_DIR/api.log" 2>&1 || true
dc logs --no-color --tail=400 "$WORKER_SERVICE" > "$OUT_DIR/worker.log" 2>&1 || true
dc logs --no-color --tail=200 frontend > "$OUT_DIR/frontend.log" 2>&1 || true
dc logs --no-color --tail=200 edge-relay > "$OUT_DIR/edge-relay.log" 2>&1 || true

if [[ -f .verify_audio_patch/report.txt ]]; then cp .verify_audio_patch/report.txt "$OUT_DIR/verify_audio_patch_report.txt"; fi
if [[ -f .verify_audio_e2e/report.txt ]]; then cp .verify_audio_e2e/report.txt "$OUT_DIR/verify_audio_e2e_report.txt"; fi

python - <<'PY'
from pathlib import Path
out = Path('artifacts/audio-ci/summary.md')
parts = ['# Audio CI fail-safe summary', '']
for path in [
    Path('artifacts/audio-ci/docker-compose-ps.txt'),
    Path('artifacts/audio-ci/verify_audio_patch_report.txt'),
    Path('artifacts/audio-ci/verify_audio_e2e_report.txt'),
]:
    parts.append(f'## {path.name}')
    if path.exists():
        content = path.read_text(encoding='utf-8', errors='ignore')[:20000]
        parts.append('```')
        parts.append(content)
        parts.append('```')
    else:
        parts.append('missing')
    parts.append('')
out.write_text('\n'.join(parts), encoding='utf-8')
print(out)
PY
