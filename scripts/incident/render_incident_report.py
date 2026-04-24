#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

NEXT_ACTIONS = {
    "provider_failure": "- Check provider status / upstream API quota / retry policy.",
    "queue_backlog": "- Check Celery worker health, Redis latency, queue depth, stuck jobs.",
    "ffmpeg_failure": "- Check input media integrity, codec handling, ffmpeg command args.",
    "infra_down": "- Check container/node/network/storage health.",
    "test_regression": "- Inspect latest code diff and failing assertions.",
    "unknown": "- No strong signal found. Inspect workflow logs manually.",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classification", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    data = json.loads(Path(args.classification).read_text(encoding="utf-8"))
    root = data.get("root_cause", "unknown")
    confidence = data.get("confidence", 0.0)
    secondary_cause = data.get("secondary_cause")
    evidence_lines = "\n".join(f"- {x}" for x in data.get("evidence", []))
    score_lines = "\n".join(
        f"- {k}: {v}" for k, v in data.get("scores", {}).items()
    )
    ranked_lines = "\n".join(
        f"- {x['cause']}: {x['score']}" for x in data.get("ranked_causes", [])
    )

    md = f"""# Auto Incident Report

- Workflow: `{data.get('workflow_name', '')}`
- Run ID: `{data.get('run_id', '')}`
- Root cause: `{root}`
- Confidence: `{confidence}`
- Secondary cause: `{secondary_cause}`

## Summary
{data.get('summary', '')}

## Ranked Causes
{ranked_lines if ranked_lines else score_lines}

## Evidence
{evidence_lines if evidence_lines else '_No evidence snippets collected._'}

## Suggested next action
{NEXT_ACTIONS.get(root, NEXT_ACTIONS['unknown'])}
"""

    Path(args.output).write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
