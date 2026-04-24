#!/usr/bin/env python3
import json
import os
from pathlib import Path


def _read_classification() -> dict:
    try:
        return json.loads(Path('.incident_classification.json').read_text(encoding='utf-8'))
    except Exception:
        return {}


def main() -> int:
    report_dir = Path('.incident_report')
    markdown_report = report_dir / 'INCIDENT_REPORT.md'
    summary = markdown_report.read_text(encoding='utf-8')[:2800] if markdown_report.exists() else 'INCIDENT_REPORT.md missing'
    run_url = f"{os.getenv('GITHUB_SERVER_URL', 'https://github.com')}/{os.getenv('GITHUB_REPOSITORY', '')}/actions/runs/{os.getenv('GITHUB_RUN_ID', '')}"

    classification = _read_classification()
    root_cause = classification.get('root_cause', 'unknown')
    confidence = classification.get('confidence', '')
    secondary_cause = classification.get('secondary_cause') or 'none'
    ai_summary = classification.get('summary', '')

    esc = classification.get('escalation', {})
    esc_mode = esc.get('mode', 'channel_only')
    esc_sev = esc.get('severity', 'P3')
    esc_team = esc.get('mention_team', 'oncall')

    primary_act = classification.get('recommended_actions', {}).get('primary', {})
    first_action = (primary_act.get('commands') or ['inspect logs'])[0]
    top_owner = (primary_act.get('owners') or ['oncall'])[0]

    link_primary = classification.get('linked_resources', {}).get('primary', {})
    runbook = link_primary.get('runbook', '')
    oncall_channel = link_primary.get('chat', {}).get('slack', '')

    payload = {
        'text': f'🚨 Audio incident: {ai_summary or "Auto incident report generated"}',
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
            {
                'type': 'section',
                'fields': [
                    {'type': 'mrkdwn', 'text': f"*Root cause:*\n`{root_cause}`"},
                    {'type': 'mrkdwn', 'text': f"*Confidence:*\n`{confidence}`"},
                    {'type': 'mrkdwn', 'text': f"*Secondary cause:*\n`{secondary_cause}`"},
                ],
            },
            {
                'type': 'section',
                'fields': [
                    {'type': 'mrkdwn', 'text': f"*Escalation:*\n`{esc_mode}` / `{esc_sev}`"},
                    {'type': 'mrkdwn', 'text': f"*Ping team:*\n`{esc_team}` / `{top_owner}`"},
                    {'type': 'mrkdwn', 'text': f"*First action:*\n{first_action}"},
                    {'type': 'mrkdwn', 'text': f"*Oncall channel:*\n{oncall_channel}"},
                ],
            },
            {'type': 'section', 'text': {'type': 'mrkdwn', 'text': f"*Runbook:* {runbook}"}},
            {'type': 'section', 'text': {'type': 'mrkdwn', 'text': f"<{run_url}|Open workflow run>"}},
            {'type': 'section', 'text': {'type': 'mrkdwn', 'text': f"*Incident summary:*\n```{summary}```"}},
        ],
    }
    print(json.dumps(payload))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
