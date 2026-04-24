#!/usr/bin/env python3
import json
import os
from pathlib import Path


def main() -> int:
    report_dir = Path('.incident_report')
    markdown_report = report_dir / 'INCIDENT_REPORT.md'
    summary = markdown_report.read_text(encoding='utf-8')[:2800] if markdown_report.exists() else 'INCIDENT_REPORT.md missing'
    run_url = f"{os.getenv('GITHUB_SERVER_URL', 'https://github.com')}/{os.getenv('GITHUB_REPOSITORY', '')}/actions/runs/{os.getenv('GITHUB_RUN_ID', '')}"

    payload = {
        'text': 'Auto incident report generated',
        'blocks': [
            {'type': 'header', 'text': {'type': 'plain_text', 'text': 'Audio Incident Report'}},
            {
                'type': 'section',
                'fields': [
                    {'type': 'mrkdwn', 'text': f"*Repo:*\n{os.getenv('GITHUB_REPOSITORY', '')}"},
                    {'type': 'mrkdwn', 'text': f"*Context:*\n{os.getenv('INCIDENT_CONTEXT', '')}"},
                    {'type': 'mrkdwn', 'text': f"*Alert:*\n{os.getenv('ALERT_NAME', '')}"},
                    {'type': 'mrkdwn', 'text': f"*Severity:*\n{os.getenv('ALERT_SEVERITY', '')}"},
                ],
            },
            {'type': 'section', 'text': {'type': 'mrkdwn', 'text': f"<{run_url}|Open workflow run>"}},
            {'type': 'section', 'text': {'type': 'mrkdwn', 'text': f"*Incident summary:*\n```{summary}```"}},
        ],
    }
    print(json.dumps(payload))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
