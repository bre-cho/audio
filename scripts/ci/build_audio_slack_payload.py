#!/usr/bin/env python3
from __future__ import annotations
import json
import os
from pathlib import Path

repo = os.getenv("GITHUB_REPOSITORY", "khong_xac_dinh/repo")
run_id = os.getenv("GITHUB_RUN_ID", "")
server = os.getenv("GITHUB_SERVER_URL", "https://github.com")
workflow = os.getenv("GITHUB_WORKFLOW", "audio-ci-e2e")
ref = os.getenv("GITHUB_REF_NAME", os.getenv("GITHUB_REF", "khong_xac_dinh"))
actor = os.getenv("GITHUB_ACTOR", "khong_xac_dinh")
job_status = os.getenv("JOB_STATUS", os.getenv("GITHUB_JOB_STATUS", "khong_xac_dinh"))

patch_report = Path('.verify_audio_patch/report.txt')
e2e_report = Path('.verify_audio_e2e/report.txt')
summary = Path('artifacts/audio-ci/summary.md')
run_url = f"{server}/{repo}/actions/runs/{run_id}" if run_id else server
artifact_hint = "Tep artifact: audio-ci-*"


def tail_text(path: Path, limit: int = 1200) -> str:
    if not path.exists():
        return f"thieu: {path}"
    text = path.read_text(encoding='utf-8', errors='ignore')
    text = text[-limit:]
    return text

patch_tail = tail_text(patch_report)
e2e_tail = tail_text(e2e_report)
status_word = "THAT_BAI" if "NO-GO" in patch_tail + e2e_tail else "DA_PHUC_HOI" if "GO" in patch_tail + e2e_tail else "CHUA_XAC_DINH"
color = "danger" if status_word == "THAT_BAI" else "good" if status_word == "DA_PHUC_HOI" else "warning"
text = f"[{status_word}] {workflow} tai {repo} ({ref})"

payload = {
    "text": text,
    "blocks": [
        {"type": "header", "text": {"type": "plain_text", "text": text}},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Repo*\n{repo}"},
                {"type": "mrkdwn", "text": f"*Nhanh*\n{ref}"},
                {"type": "mrkdwn", "text": f"*Nguoi chay*\n{actor}"},
                {"type": "mrkdwn", "text": f"*Lan chay*\n<{run_url}|Mo lan chay>"},
            ],
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Goi y artifact*\n{artifact_hint}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": "*Doan cuoi verify_audio_patch*\n```" + patch_tail.replace('```', "'''") + "```"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": "*Doan cuoi verify_audio_e2e*\n```" + e2e_tail.replace('```', "'''") + "```"}},
    ],
    "attachments": [
        {
            "color": color,
            "blocks": [
                {"type": "context", "elements": [{"type": "mrkdwn", "text": f"tep tong hop: {summary.as_posix()}"}]}
            ],
        }
    ],
}
print(json.dumps(payload, ensure_ascii=False))
