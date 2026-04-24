#!/usr/bin/env bash
set -euo pipefail

REPORT_DIR="${REPORT_DIR:-.incident_report}"
mkdir -p "${REPORT_DIR}/logs" "${REPORT_DIR}/http" "${REPORT_DIR}/meta"

timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "${timestamp}" > "${REPORT_DIR}/meta/generated_at.txt"
echo "${INCIDENT_CONTEXT:-unknown}" > "${REPORT_DIR}/meta/incident_context.txt"
echo "${ALERT_NAME:-}" > "${REPORT_DIR}/meta/alert_name.txt"
echo "${ALERT_SEVERITY:-warning}" > "${REPORT_DIR}/meta/alert_severity.txt"

git rev-parse HEAD > "${REPORT_DIR}/meta/git_sha.txt" 2>/dev/null || true
git status --short > "${REPORT_DIR}/meta/git_status.txt" 2>/dev/null || true

${DOCKER_COMPOSE_BIN:-docker compose} ps > "${REPORT_DIR}/docker_compose_ps.txt" 2>&1 || true

for svc in "${API_SERVICE:-api}" "${WORKER_SERVICE:-worker}" "${FRONTEND_SERVICE:-frontend}" "${EDGE_RELAY_SERVICE:-edge-relay}" "${REDIS_SERVICE:-redis}" "${POSTGRES_SERVICE:-postgres}"; do
  ${DOCKER_COMPOSE_BIN:-docker compose} logs --tail=300 "$svc" > "${REPORT_DIR}/logs/${svc}.log" 2>&1 || true
done

if [[ -n "${BASE_URL:-}" ]]; then
  curl -fsS "${BASE_URL}/healthz" > "${REPORT_DIR}/http/healthz.json" 2> "${REPORT_DIR}/http/healthz.err" || true
  curl -fsS "${BASE_URL}/api/v1/audio/health" > "${REPORT_DIR}/http/audio_health.json" 2> "${REPORT_DIR}/http/audio_health.err" || true
  curl -fsS "${BASE_URL}/metrics" > "${REPORT_DIR}/http/metrics.txt" 2> "${REPORT_DIR}/http/metrics.err" || true
fi

if [[ -n "${ALERTMANAGER_URL:-}" ]]; then
  curl -fsS "${ALERTMANAGER_URL}/api/v2/alerts" > "${REPORT_DIR}/http/alertmanager_alerts.json" 2> "${REPORT_DIR}/http/alertmanager_alerts.err" || true
  curl -fsS "${ALERTMANAGER_URL}/api/v2/silences" > "${REPORT_DIR}/http/alertmanager_silences.json" 2> "${REPORT_DIR}/http/alertmanager_silences.err" || true
fi

if [[ -n "${PROMETHEUS_URL:-}" ]]; then
  curl -fsS --get "${PROMETHEUS_URL}/api/v1/query" --data-urlencode 'query=up' > "${REPORT_DIR}/http/prom_up.json" 2> "${REPORT_DIR}/http/prom_up.err" || true
  curl -fsS --get "${PROMETHEUS_URL}/api/v1/query" --data-urlencode 'query=sum(rate(audio_preview_failure_total[10m]))' > "${REPORT_DIR}/http/prom_audio_preview_fail_rate.json" 2> "${REPORT_DIR}/http/prom_audio_preview_fail_rate.err" || true
  curl -fsS --get "${PROMETHEUS_URL}/api/v1/query" --data-urlencode 'query=sum(rate(audio_narration_failure_total[10m]))' > "${REPORT_DIR}/http/prom_audio_narration_fail_rate.json" 2> "${REPORT_DIR}/http/prom_audio_narration_fail_rate.err" || true
  curl -fsS --get "${PROMETHEUS_URL}/api/v1/query" --data-urlencode 'query=audio_narration_stuck_jobs' > "${REPORT_DIR}/http/prom_audio_stuck_jobs.json" 2> "${REPORT_DIR}/http/prom_audio_stuck_jobs.err" || true
fi
