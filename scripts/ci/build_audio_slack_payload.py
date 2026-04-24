#!/usr/bin/env python3
from __future__ import annotations
import json
import os
from pathlib import Path

repo = os.getenv("GITHUB_REPOSITORY", "unknown/repo")
run_id = os.getenv("GITHUB_RUN_ID", "")
server = os.getenv("GITHUB_SERVER_URL", "https://github.com")
workflow = os.getenv("GITHUB_WORKFLOW", "audio-ci-e2e")
ref = os.getenv("GITHUB_REF_NAME", os.getenv("GITHUB_REF", "unknown"))
actor = os.getenv("GITHUB_ACTOR", "unknown")
job_status = os.getenv("JOB_STATUS", os.getenv("GITHUB_JOB_STATUS", "unknown"))

patch_report = Path('.verify_audio_patch/report.txt')
e2e_report = Path('.verify_audio_e2e/report.txt')
summary = Path('artifacts/audio-ci/summary.md')
run_url = f"{server}/{repo}/actions/runs/{run_id}" if run_id else server
artifact_hint = "Artifacts: audio-ci-*"


def tail_text(path: Path, limit: int = 1200) -> str:
    if not path.exists():
        return f"missing: {path}"
    text = path.read_text(encoding='utf-8', errors='ignore')
    text = text[-limit:]
    return text

patch_tail = tail_text(patch_report)
e2e_tail = tail_text(e2e_report)
status_word = "FAILED" if "NO-GO" in patch_tail + e2e_tail else "RECOVERED" if "GO" in patch_tail + e2e_tail else "UNKNOWN"
color = "danger" if status_word == "FAILED" else "good" if status_word == "RECOVERED" else "warning"
text = f"[{status_word}] {workflow} on {repo} ({ref})"

payload = {
    "text": text,
    "blocks": [
        {"type": "header", "text": {"type": "plain_text", "text": text}},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Repo*\n{repo}"},
                {"type": "mrkdwn", "text": f"*Branch*\n{ref}"},
                {"type": "mrkdwn", "text": f"*Actor*\n{actor}"},
                {"type": "mrkdwn", "text": f"*Run*\n<{run_url}|Open run>"},
            ],
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Artifact hint*\n{artifact_hint}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": "*verify_audio_patch tail*\n```" + patch_tail.replace('```', "'''") + "```"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": "*verify_audio_e2e tail*\n```" + e2e_tail.replace('```', "'''") + "```"}},
    ],
    "attachments": [
        {
            "color": color,
            "blocks": [
                {"type": "context", "elements": [{"type": "mrkdwn", "text": f"summary file: {summary.as_posix()}"}]}
            ],
        }
    ],
}
print(json.dumps(payload, ensure_ascii=False))
