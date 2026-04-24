#!/usr/bin/env bash
set -Eeuo pipefail

# verify_audio_patch.sh
# Goal: quick GO/NO-GO verification for the audio patch round.
# Usage:
#   bash verify_audio_patch.sh
# Optional env vars:
#   API_SERVICE=api WORKER_SERVICE=worker STACK_WAIT_SECONDS=8 \
#   PYTHON_BIN=python DOCKER_COMPOSE_BIN='docker compose' bash verify_audio_patch.sh

API_SERVICE="${API_SERVICE:-api}"
WORKER_SERVICE="${WORKER_SERVICE:-worker}"
STACK_WAIT_SECONDS="${STACK_WAIT_SECONDS:-8}"
PYTHON_BIN="${PYTHON_BIN:-python}"
DOCKER_COMPOSE_BIN="${DOCKER_COMPOSE_BIN:-docker compose}"
BACKEND_ROOT="${BACKEND_ROOT:-backend/app}"
OUT_DIR="${OUT_DIR:-.verify_audio_patch}"

mkdir -p "$OUT_DIR"
REPORT="$OUT_DIR/report.txt"
: > "$REPORT"

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

red() { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
blue() { printf '\033[34m%s\033[0m\n' "$*"; }

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  green "PASS  $*"
  printf 'PASS  %s\n' "$*" >> "$REPORT"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  red "FAIL  $*"
  printf 'FAIL  %s\n' "$*" >> "$REPORT"
}

warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  yellow "WARN  $*"
  printf 'WARN  %s\n' "$*" >> "$REPORT"
}

section() {
  printf '\n' | tee -a "$REPORT" >/dev/null
  blue "== $* =="
  printf '== %s ==\n' "$*" >> "$REPORT"
}

run_cmd() {
  local name="$1"
  shift
  local log_file="$OUT_DIR/${name}.log"
  printf '\n$ %s\n' "$*" >> "$REPORT"
  if "$@" >"$log_file" 2>&1; then
    pass "$name"
    return 0
  fi
  fail "$name"
  printf '%s\n' "--- ${name}.log ---" >> "$REPORT"
  tail -n 80 "$log_file" >> "$REPORT" || true
  return 1
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

compose_up() {
  bash -lc "$DOCKER_COMPOSE_BIN up -d"
}

compose_exec() {
  local service="$1"
  shift
  bash -lc "$DOCKER_COMPOSE_BIN exec -T $service $*"
}

compose_logs() {
  local service="$1"
  local lines="$2"
  bash -lc "$DOCKER_COMPOSE_BIN logs --tail=$lines $service"
}

section "Preflight"
if [[ ! -d "$BACKEND_ROOT" ]]; then
  fail "backend root not found: $BACKEND_ROOT"
  echo "Expected to run from repo root. Override BACKEND_ROOT if needed." >> "$REPORT"
  printf '\nGO/NO-GO: NO-GO\n' | tee -a "$REPORT"
  exit 1
else
  pass "backend root exists: $BACKEND_ROOT"
fi

if [[ -f docker-compose.yml || -f compose.yml || -f compose.yaml ]]; then
  pass "compose file present"
else
  warn "compose file not found in current directory"
fi

if command_exists git; then
  run_cmd git_status git status --short || true
else
  warn "git not found"
fi

if command_exists "$PYTHON_BIN"; then
  pass "python available: $PYTHON_BIN"
else
  fail "python not found: $PYTHON_BIN"
fi

section "Static checks"
run_cmd compileall "$PYTHON_BIN" -m compileall "$BACKEND_ROOT" || true

cat > "$OUT_DIR/import_check.py" <<'PY'
import importlib
mods = [
    "backend.app.api.audio",
    "backend.app.services.audio.voice_clone_service",
    "backend.app.services.audio.narration_service",
]
failed = []
for mod in mods:
    try:
        importlib.import_module(mod)
        print(f"OK {mod}")
    except Exception as exc:
        failed.append((mod, exc))
        print(f"FAIL {mod}: {exc}")
if failed:
    raise SystemExit(1)
PY
run_cmd import_modules "$PYTHON_BIN" "$OUT_DIR/import_check.py" || true

section "Patch surface check"
for f in \
  backend/app/api/audio.py \
  backend/app/services/audio/voice_clone_service.py \
  backend/app/services/audio/narration_service.py
  do
    if [[ -f "$f" ]]; then
      pass "file exists: $f"
    else
      fail "missing file: $f"
    fi
  done

if grep -R "combined_audio += audio_bytes" backend/app/services/audio/narration_service.py >/dev/null 2>&1; then
  fail "legacy mp3 byte concatenation still present"
else
  pass "legacy mp3 byte concatenation removed"
fi

if grep -R "run_narration_job(db, row.id)" backend/app/api/audio.py >/dev/null 2>&1; then
  fail "audio API still appears to run narration synchronously"
else
  pass "audio API no longer shows legacy sync narration call"
fi

if grep -R "Path(tmpdir) / file.filename" backend/app/api/audio.py >/dev/null 2>&1; then
  fail "unsafe upload filename handling still present"
else
  pass "unsafe upload filename pattern not found"
fi

section "Container checks"
if command_exists docker; then
  run_cmd compose_up compose_up || true
  sleep "$STACK_WAIT_SECONDS"

  run_cmd api_compile_in_container compose_exec "$API_SERVICE" "$PYTHON_BIN -m compileall $BACKEND_ROOT" || true
  run_cmd ffmpeg_in_api compose_exec "$API_SERVICE" "ffmpeg -version | head -n 1" || true

  if compose_logs "$API_SERVICE" 120 >"$OUT_DIR/api_logs.log" 2>&1; then
    pass "api logs captured"
  else
    warn "could not capture api logs"
  fi

  if compose_logs "$WORKER_SERVICE" 160 >"$OUT_DIR/worker_logs.log" 2>&1; then
    pass "worker logs captured"
  else
    warn "could not capture worker logs"
  fi

  if [[ -f "$OUT_DIR/worker_logs.log" ]]; then
    if grep -Ei "error|traceback|exception" "$OUT_DIR/worker_logs.log" >/dev/null 2>&1; then
      warn "worker logs contain error-like lines; inspect $OUT_DIR/worker_logs.log"
    else
      pass "worker logs do not show obvious error markers in tail"
    fi
  fi
else
  warn "docker not found; skipping container checks"
fi

section "Pytest"
if command_exists pytest; then
  run_cmd pytest_audio pytest -q -k "audio or narration or voice_clone" || warn "pytest audio selection failed or no tests matched"
else
  warn "pytest not found"
fi

section "Summary"
printf 'PASS=%d\nFAIL=%d\nWARN=%d\n' "$PASS_COUNT" "$FAIL_COUNT" "$WARN_COUNT" | tee -a "$REPORT"

if (( FAIL_COUNT > 0 )); then
  printf '\nGO/NO-GO: NO-GO\n' | tee -a "$REPORT"
  cat <<TXT | tee -a "$REPORT"
Blocking conditions detected. Check these logs first:
- $OUT_DIR/compileall.log
- $OUT_DIR/import_modules.log
- $OUT_DIR/api_compile_in_container.log
- $OUT_DIR/ffmpeg_in_api.log
- $OUT_DIR/worker_logs.log
TXT
  exit 1
fi

printf '\nGO/NO-GO: GO\n' | tee -a "$REPORT"
cat <<TXT | tee -a "$REPORT"
Core checks passed.
Suggested next manual checks:
1) Hit preview endpoint and confirm preview_url is returned.
2) Queue a narration job and confirm worker consumes it.
3) Run ffprobe on one final audio output.
TXT
