#!/usr/bin/env bash
set -euo pipefail

REPORT_DIR="${REPORT_DIR:-.incident_report}"
REPORT_MD="${REPORT_DIR}/INCIDENT_REPORT.md"

python - <<'PY'
from pathlib import Path
import json, re

report_dir = Path(".incident_report")
out = report_dir / "INCIDENT_REPORT.md"

def read_text(path):
    p = report_dir / path
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def read_json(path):
    txt = read_text(path)
    if not txt.strip():
        return None
    try:
        return json.loads(txt)
    except Exception:
        return None

def extract_metric(name):
    txt = read_text("http/metrics.txt")
    pattern = re.compile(rf"^{re.escape(name)}(?:\{{.*?\}})?\s+([0-9eE+\-.]+)$", re.M)
    vals = []
    for m in pattern.finditer(txt):
        try:
            vals.append(float(m.group(1)))
        except Exception:
            pass
    return vals

generated_at = read_text("meta/generated_at.txt").strip() or "unknown"
context = read_text("meta/incident_context.txt").strip() or "unknown"
alert_name = read_text("meta/alert_name.txt").strip() or "unknown"
severity = read_text("meta/alert_severity.txt").strip() or "warning"
git_sha = read_text("meta/git_sha.txt").strip() or "unknown"

healthz = read_text("http/healthz.json")
audio_health = read_text("http/audio_health.json")
docker_ps = read_text("docker_compose_ps.txt")
alerts = read_json("http/alertmanager_alerts.json") or []
preview_req = extract_metric("audio_preview_requests_total")
preview_fail = extract_metric("audio_preview_failure_total")
narr_req = extract_metric("audio_narration_requests_total")
narr_fail = extract_metric("audio_narration_failure_total")
stuck_jobs = extract_metric("audio_narration_stuck_jobs")

suspicions = []
if not healthz.strip() or "error" in healthz.lower():
    suspicions.append("Base health endpoint is failing or empty.")
if not audio_health.strip() or "error" in audio_health.lower():
    suspicions.append("Audio health endpoint is failing or empty.")
if preview_fail and sum(preview_fail) > 0:
    suspicions.append("Preview failures are present in realtime metrics.")
if narr_fail and sum(narr_fail) > 0:
    suspicions.append("Narration failures are present in realtime metrics.")
if stuck_jobs and max(stuck_jobs) > 0:
    suspicions.append(f"Audio stuck jobs detected: max={max(stuck_jobs)}.")
if "Exit" in docker_ps or "unhealthy" in docker_ps.lower():
    suspicions.append("At least one compose service looks exited or unhealthy.")

top_alerts = []
for a in alerts[:10]:
    labels = a.get("labels", {})
    ann = a.get("annotations", {})
    top_alerts.append(
        f"- {labels.get('alertname','unknown')} | component={labels.get('component','')} | "
        f"provider={labels.get('provider','')} | severity={labels.get('severity','')} | "
        f"summary={ann.get('summary','')}"
    )

lines = []
lines.append("# Incident Report")
lines.append("")
lines.append(f"- Generated at: `{generated_at}`")
lines.append(f"- Context: `{context}`")
lines.append(f"- Alert name: `{alert_name}`")
lines.append(f"- Severity: `{severity}`")
lines.append(f"- Git SHA: `{git_sha}`")
lines.append("")
lines.append("## Executive summary")
if suspicions:
    for s in suspicions[:8]:
        lines.append(f"- {s}")
else:
    lines.append("- No strong failure signal was inferred from the collected snapshots.")
lines.append("")
lines.append("## Active alerts snapshot")
if top_alerts:
    lines.extend(top_alerts)
else:
    lines.append("- No active alerts snapshot available.")
lines.append("")
lines.append("## Metrics snapshot")
lines.append(f"- audio_preview_requests_total: {preview_req or ['n/a']}")
lines.append(f"- audio_preview_failure_total: {preview_fail or ['n/a']}")
lines.append(f"- audio_narration_requests_total: {narr_req or ['n/a']}")
lines.append(f"- audio_narration_failure_total: {narr_fail or ['n/a']}")
lines.append(f"- audio_narration_stuck_jobs: {stuck_jobs or ['n/a']}")
lines.append("")
lines.append("## Endpoint snapshot")
lines.append("### /healthz")
lines.append("```json")
lines.append((healthz[:4000] or "n/a"))
lines.append("```")
lines.append("")
lines.append("### /api/v1/audio/health")
lines.append("```json")
lines.append((audio_health[:4000] or "n/a"))
lines.append("```")
lines.append("")
lines.append("## Compose snapshot")
lines.append("```text")
lines.append((docker_ps[:4000] or "n/a"))
lines.append("```")
lines.append("")
lines.append("## Suggested next actions")
for s in [
    "Check api and worker logs in .incident_report/logs/.",
    "If preview failed, inspect provider credentials and audio provider error normalization.",
    "If narration failed, inspect ffmpeg availability and audio merge path.",
    "If stuck jobs > 0, inspect worker queue consumption and Redis health.",
    "If provider-specific alerts are present, consider routing traffic away from the failing provider.",
]:
    lines.append(f"- {s}")

out.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {out}")
PY

echo "Incident report generated at ${REPORT_MD}"
