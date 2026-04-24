#!/usr/bin/env python3
import json
import os
from pathlib import Path


def main() -> int:
    report_dir = Path('.audio_synthetic_probe')
    status_file = report_dir / 'status.txt'
    status_text = status_file.read_text(encoding='utf-8').strip() if status_file.exists() else 'status report missing'
    run_url = f"{os.getenv('GITHUB_SERVER_URL', 'https://github.com')}/{os.getenv('GITHUB_REPOSITORY', '')}/actions/runs/{os.getenv('GITHUB_RUN_ID', '')}"
    payload = {
        'text': 'Audio health monitor failed',
        'blocks': [
            {'type': 'header', 'text': {'type': 'plain_text', 'text': 'Audio Health Monitor Failed'}},
            {
                'type': 'section',
                'fields': [
                    {'type': 'mrkdwn', 'text': f"*Repo:*\n{os.getenv('GITHUB_REPOSITORY', '')}"},
                    {'type': 'mrkdwn', 'text': f"*Workflow:*\n{os.getenv('GITHUB_WORKFLOW', '')}"},
                    {'type': 'mrkdwn', 'text': f"*Run:*\n<{run_url}|Open run>"},
                    {'type': 'mrkdwn', 'text': f"*Base URL:*\n{os.getenv('BASE_URL', '')}"},
                ],
            },
            {'type': 'section', 'text': {'type': 'mrkdwn', 'text': f"*Probe status:*\n```{status_text[:2800]}```"}},
        ],
    }
    print(json.dumps(payload))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
