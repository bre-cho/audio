#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


MAX_CONFIDENCE = 0.99
GAP_WEIGHT = 0.08
SECONDARY_CAUSE_THRESHOLD = 0.35

ACTION_MAP = {
    "provider_failure": {
        "commands": ["check provider quota/status", "retry failed job once"],
        "dashboards": ["provider api latency", "provider error rate"],
        "services": ["provider adapter", "webhook/egress"],
        "owners": ["ai-platform", "integrations"],
    },
    "queue_backlog": {
        "commands": ["celery inspect active", "redis-cli info", "scale worker"],
        "dashboards": ["queue depth", "worker concurrency"],
        "services": ["celery worker", "redis"],
        "owners": ["platform", "backend"],
    },
    "ffmpeg_failure": {
        "commands": ["inspect ffmpeg stderr", "re-run render with debug args"],
        "dashboards": ["render failure rate", "media pipeline"],
        "services": ["render worker", "ffmpeg wrapper"],
        "owners": ["media", "backend"],
    },
    "infra_down": {
        "commands": ["kubectl get pods", "kubectl describe failing pod", "check disk/memory"],
        "dashboards": ["node health", "container restarts"],
        "services": ["k8s/api", "storage/network"],
        "owners": ["sre", "platform"],
    },
    "test_regression": {
        "commands": ["open failing test logs", "git diff HEAD~1..HEAD", "re-run failed suite"],
        "dashboards": ["ci failures", "test trend"],
        "services": ["ci runner", "test suite"],
        "owners": ["backend", "qa"],
    },
    "unknown": {
        "commands": ["open workflow logs", "inspect latest artifacts"],
        "dashboards": ["workflow overview"],
        "services": ["unknown"],
        "owners": ["oncall"],
    },
}

LINK_MAP = {
    "provider_failure": {
        "runbook": "docs/runbooks/provider_failure.md",
        "dashboards": {
            "grafana": "https://grafana.example.com/d/provider-api",
            "sentry": "https://sentry.example.com/issues/?query=provider",
        },
        "logs": {
            "loki": "https://grafana.example.com/explore?query=provider",
            "kibana": "https://kibana.example.com/app/discover#/provider",
        },
        "chat": {"slack": "#ai-integrations-alerts", "oncall": "ai-platform-oncall"},
    },
    "queue_backlog": {
        "runbook": "docs/runbooks/queue_backlog.md",
        "dashboards": {
            "grafana": "https://grafana.example.com/d/queue-depth",
            "metabase": "https://metabase.example.com/question/queue-depth",
        },
        "logs": {
            "loki": "https://grafana.example.com/explore?query=celery",
            "kibana": "https://kibana.example.com/app/discover#/redis-celery",
        },
        "chat": {"slack": "#platform-oncall", "oncall": "platform-oncall"},
    },
    "ffmpeg_failure": {
        "runbook": "docs/runbooks/ffmpeg_failure.md",
        "dashboards": {
            "grafana": "https://grafana.example.com/d/render-pipeline",
            "sentry": "https://sentry.example.com/issues/?query=ffmpeg",
        },
        "logs": {
            "loki": "https://grafana.example.com/explore?query=ffmpeg",
            "kibana": "https://kibana.example.com/app/discover#/ffmpeg",
        },
        "chat": {"slack": "#media-pipeline", "oncall": "media-oncall"},
    },
    "infra_down": {
        "runbook": "docs/runbooks/infra_down.md",
        "dashboards": {
            "grafana": "https://grafana.example.com/d/node-health",
            "metabase": "https://metabase.example.com/question/restarts",
        },
        "logs": {
            "loki": "https://grafana.example.com/explore?query=kubernetes",
            "kibana": "https://kibana.example.com/app/discover#/infra",
        },
        "chat": {"slack": "#sre-oncall", "oncall": "sre-primary"},
    },
    "test_regression": {
        "runbook": "docs/runbooks/test_regression.md",
        "dashboards": {
            "grafana": "https://grafana.example.com/d/ci-health",
            "sentry": "https://sentry.example.com/issues/?query=test",
        },
        "logs": {
            "loki": "https://grafana.example.com/explore?query=pytest",
            "kibana": "https://kibana.example.com/app/discover#/ci",
        },
        "chat": {"slack": "#backend-ci", "oncall": "backend-oncall"},
    },
    "unknown": {
        "runbook": "docs/runbooks/general_triage.md",
        "dashboards": {"grafana": "https://grafana.example.com/d/workflow-overview"},
        "logs": {
            "loki": "https://grafana.example.com/explore",
            "kibana": "https://kibana.example.com/app/discover",
        },
        "chat": {"slack": "#oncall", "oncall": "primary-oncall"},
    },
}

ESCALATION_POLICY = {
    "provider_failure": {"default_severity": "P2", "min_confidence_for_oncall": 0.65, "channel_only_below": 0.45},
    "queue_backlog": {"default_severity": "P2", "min_confidence_for_oncall": 0.60, "channel_only_below": 0.40},
    "ffmpeg_failure": {"default_severity": "P2", "min_confidence_for_oncall": 0.70, "channel_only_below": 0.50},
    "infra_down": {"default_severity": "P1", "min_confidence_for_oncall": 0.55, "channel_only_below": 0.35},
    "test_regression": {"default_severity": "P3", "min_confidence_for_oncall": 0.80, "channel_only_below": 0.60},
    "unknown": {"default_severity": "P3", "min_confidence_for_oncall": 0.90, "channel_only_below": 0.75},
}


def decide_escalation(root, confidence, workflow, severity_hint=None):
    p = ESCALATION_POLICY.get(root, ESCALATION_POLICY["unknown"])
    sev = severity_hint or p["default_severity"]
    if workflow == "audio-canary-deploy" and root == "infra_down":
        sev = "P1"
    if workflow in {"audio-chaos-ci", "audio-ci-e2e"} and sev == "P3" and confidence >= 0.85:
        sev = "P2"
    if root == "unknown" and confidence < p["channel_only_below"]:
        mode = "suppress"
    elif confidence < p["min_confidence_for_oncall"]:
        mode = "channel_only"
    else:
        mode = "page_oncall"
    if workflow == "audio-canary-deploy" and confidence >= 0.70:
        mode = "page_oncall"
    return {"severity": sev, "mode": mode}


def pick_top(scores):
    ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    total = sum(max(v, 0) for _, v in ordered) or 1
    primary, secondary = ordered[0], ordered[1]
    gap = primary[1] - secondary[1]
    confidence = (
        round(
            min(MAX_CONFIDENCE, max(0.0, (primary[1] / total) + (gap * GAP_WEIGHT))),
            2,
        )
        if primary[1] > 0
        else 0.0
    )
    return ordered, primary, secondary, confidence


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    ev = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    scores = {
        "provider_failure": 0,
        "queue_backlog": 0,
        "ffmpeg_failure": 0,
        "infra_down": 0,
        "test_regression": 0,
    }

    failed_steps = " | ".join(ev.get("failed_step_names", [])).lower()
    job_map = json.dumps(ev.get("job_conclusion_map", {})).lower()
    provider = json.dumps(ev.get("provider_health", {})).lower()
    queue = json.dumps(ev.get("queue_snapshot", {})).lower()
    ffmpeg = json.dumps(ev.get("ffmpeg_stderr", [])).lower()
    blob = "\n".join([failed_steps, job_map, provider, queue, ffmpeg])

    if "degraded" in provider or re.search(
        r"openai|elevenlabs|runway|veo|kling|429|503|timeout|upstream", blob
    ):
        scores["provider_failure"] += 4
    if re.search(
        r"redis|celery|worker.*offline|queue backlog|pending too long|degraded", queue
    ):
        scores["queue_backlog"] += 4
    if re.search(
        r"ffmpeg|conversion failed|moov atom not found|invalid data|decode", ffmpeg
    ):
        scores["ffmpeg_failure"] += 5
    if re.search(
        r"connection refused|no route to host|oomkilled|disk full|name resolution", blob
    ):
        scores["infra_down"] += 4
    if re.search(
        r"pytest|assert|snapshot mismatch|smoke test failed|e2e.*failed", failed_steps
    ):
        scores["test_regression"] += 4

    ordered, primary, secondary, confidence = pick_top(scores)
    root = primary[0] if primary[1] > 0 else "unknown"

    secondary_cause = secondary[0] if secondary[1] > 0 else None
    if secondary[1] <= 0 or secondary[1] < max(1, int(primary[1] * SECONDARY_CAUSE_THRESHOLD)):
        secondary_cause = None

    evidence_snippets = []
    if ev.get("failed_step_names"):
        evidence_snippets.extend(ev["failed_step_names"][:3])
    if ev.get("ffmpeg_stderr"):
        evidence_snippets.extend(
            [
                x["stderr_lines"][0]
                for x in ev["ffmpeg_stderr"][:2]
                if x.get("stderr_lines")
            ]
        )
    if not evidence_snippets and ev.get("queue_snapshot", {}).get("signals"):
        evidence_snippets.extend(ev["queue_snapshot"]["signals"][:2])

    # Recommended actions (v5)
    primary_actions = dict(ACTION_MAP.get(root, ACTION_MAP["unknown"]))
    primary_actions["commands"] = list(primary_actions["commands"])
    if root == "ffmpeg_failure" and secondary_cause == "provider_failure":
        primary_actions["commands"].insert(
            0, "check whether corrupt upstream asset caused ffmpeg decode failure"
        )
    if root == "queue_backlog" and secondary_cause == "infra_down":
        primary_actions["commands"].insert(
            0, "check whether worker/node pressure is causing queue drain failure"
        )
    secondary_actions = ACTION_MAP.get(secondary_cause) if secondary_cause else None

    # Linked resources (v6) — inject run_id into log URLs
    run_id = ev.get("run_id", "")
    workflow_name = ev.get("workflow_name", "")
    primary_links = {
        k: (dict(v) if isinstance(v, dict) else v)
        for k, v in LINK_MAP.get(root, LINK_MAP["unknown"]).items()
    }
    primary_links["logs"] = dict(primary_links.get("logs", {}))
    if primary_links["logs"].get("loki"):
        primary_links["logs"]["loki"] += f"&run_id={run_id}"
    if primary_links["logs"].get("kibana"):
        primary_links["logs"]["kibana"] += f"?run_id={run_id}"
    if workflow_name == "audio-canary-deploy" and root == "infra_down":
        primary_links.setdefault("dashboards", {})["grafana"] = (
            "https://grafana.example.com/d/canary-deploy"
        )
    secondary_links = (
        LINK_MAP.get(secondary_cause) if secondary_cause else None
    )

    # Escalation policy (v7)
    severity_hint = "P1" if workflow_name == "audio-canary-deploy" else None
    escalation = decide_escalation(root, confidence, workflow_name, severity_hint)
    mention_team = (primary_actions.get("owners") or ["oncall"])[0]
    dedupe_key = f'{workflow_name}::{root}::{secondary_cause}::{escalation["severity"]}'

    out = {
        "workflow_name": workflow_name,
        "run_id": run_id,
        "root_cause": root,
        "confidence": confidence,
        "secondary_cause": secondary_cause,
        "ranked_causes": [{"cause": k, "score": v} for k, v in ordered],
        "scores": scores,
        "evidence": evidence_snippets[:5],
        "summary": (
            f"{workflow_name} failed; root_cause={root}; "
            f"confidence={confidence}; secondary_cause={secondary_cause}"
        ),
        "recommended_actions": {
            "primary": primary_actions,
            "secondary": secondary_actions,
        },
        "linked_resources": {
            "primary": primary_links,
            "secondary": secondary_links,
        },
        "escalation": {
            **escalation,
            "mention_team": mention_team,
        },
        "dedupe_key": dedupe_key,
    }
    Path(args.output).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
