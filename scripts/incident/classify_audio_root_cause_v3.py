#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


MAX_CONFIDENCE = 0.99
GAP_WEIGHT = 0.08
SECONDARY_CAUSE_THRESHOLD = 0.35


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

    out = {
        "workflow_name": ev.get("workflow_name"),
        "run_id": ev.get("run_id"),
        "root_cause": root,
        "confidence": confidence,
        "secondary_cause": secondary_cause,
        "ranked_causes": [{"cause": k, "score": v} for k, v in ordered],
        "scores": scores,
        "evidence": evidence_snippets[:5],
        "summary": (
            f'{ev.get("workflow_name")} failed; root_cause={root}; '
            f"confidence={confidence}; secondary_cause={secondary_cause}"
        ),
    }
    Path(args.output).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
