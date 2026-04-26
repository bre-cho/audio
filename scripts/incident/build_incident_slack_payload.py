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
    summary = markdown_report.read_text(encoding='utf-8')[:2800] if markdown_report.exists() else 'Khong tim thay INCIDENT_REPORT.md'
    run_url = f"{os.getenv('GITHUB_SERVER_URL', 'https://github.com')}/{os.getenv('GITHUB_REPOSITORY', '')}/actions/runs/{os.getenv('GITHUB_RUN_ID', '')}"

    classification = _read_classification()
    root_cause = classification.get('root_cause', 'khong_xac_dinh')
    confidence = classification.get('confidence', '')
    secondary_cause = classification.get('secondary_cause') or 'khong_co'
    ai_summary = classification.get('summary', '')

    esc = classification.get('escalation', {})
    esc_mode = esc.get('mode', 'chi_kenh')
    esc_sev = esc.get('severity', 'P3')
    esc_team = esc.get('mention_team', 'truc_oncall')

    primary_act = classification.get('recommended_actions', {}).get('primary', {})
    first_action = (primary_act.get('commands') or ['kiem_tra_log'])[0]
    top_owner = (primary_act.get('owners') or ['truc_oncall'])[0]

    link_primary = classification.get('linked_resources', {}).get('primary', {})
    runbook = link_primary.get('runbook', '')
    oncall_channel = link_primary.get('chat', {}).get('slack', '')

    payload = {
        'text': f'🚨 Su co am thanh: {ai_summary or "Da tao bao cao su co tu dong"}',
        'blocks': [
            {'type': 'header', 'text': {'type': 'plain_text', 'text': 'Bao Cao Su Co Am Thanh'}},
            {
                'type': 'section',
                'fields': [
                    {'type': 'mrkdwn', 'text': f"*Repo:*\n{os.getenv('GITHUB_REPOSITORY', '')}"},
                    {'type': 'mrkdwn', 'text': f"*Ngu canh:*\n{os.getenv('INCIDENT_CONTEXT', '')}"},
                    {'type': 'mrkdwn', 'text': f"*Canh bao:*\n{os.getenv('ALERT_NAME', '')}"},
                    {'type': 'mrkdwn', 'text': f"*Muc do:*\n{os.getenv('ALERT_SEVERITY', '')}"},
                ],
            },
            {
                'type': 'section',
                'fields': [
                    {'type': 'mrkdwn', 'text': f"*Nguyen nhan goc:*\n`{root_cause}`"},
                    {'type': 'mrkdwn', 'text': f"*Do tin cay:*\n`{confidence}`"},
                    {'type': 'mrkdwn', 'text': f"*Nguyen nhan phu:*\n`{secondary_cause}`"},
                ],
            },
            {
                'type': 'section',
                'fields': [
                    {'type': 'mrkdwn', 'text': f"*Huong xu ly nang cap:*\n`{esc_mode}` / `{esc_sev}`"},
                    {'type': 'mrkdwn', 'text': f"*Nhom can ping:*\n`{esc_team}` / `{top_owner}`"},
                    {'type': 'mrkdwn', 'text': f"*Hanh dong dau tien:*\n{first_action}"},
                    {'type': 'mrkdwn', 'text': f"*Kenh oncall:*\n{oncall_channel}"},
                ],
            },
            {'type': 'section', 'text': {'type': 'mrkdwn', 'text': f"*Tai lieu huong dan:* {runbook}"}},
            {'type': 'section', 'text': {'type': 'mrkdwn', 'text': f"<{run_url}|Mo lan chay workflow>"}},
            {'type': 'section', 'text': {'type': 'mrkdwn', 'text': f"*Tom tat su co:*\n```{summary}```"}},
        ],
    }
    print(json.dumps(payload))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
