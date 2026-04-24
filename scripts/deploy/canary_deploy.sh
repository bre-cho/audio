#!/usr/bin/env bash
set -euo pipefail

MODE=${1:-deploy}
mkdir -p .audio_canary

run_fetch_stable() {
  bash -lc "$FETCH_STABLE_COMMAND"
}

run_canary_deploy() {
  echo "[audio-canary] deploy canary revision"
  bash -lc "$CANARY_DEPLOY_COMMAND" | tee .audio_canary/deploy.log
}

case "$MODE" in
  fetch-stable)
    run_fetch_stable
    ;;
  deploy)
    run_canary_deploy
    ;;
  *)
    echo "unknown mode: $MODE" >&2
    exit 1
    ;;
esac
