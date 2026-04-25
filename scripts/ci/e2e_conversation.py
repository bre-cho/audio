from __future__ import annotations

import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8000')
REPORT_DIR = Path(os.environ.get('REPORT_DIR', '.audio_factory_report'))
POLL_ATTEMPTS = int(os.environ.get('CONVERSATION_POLL_ATTEMPTS', '40'))
POLL_INTERVAL = float(os.environ.get('CONVERSATION_POLL_INTERVAL', '0.5'))


def _request(method: str, path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    request = Request(f'{BASE_URL}{path}', data=data, method=method)
    request.add_header('Content-Type', 'application/json')
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode('utf-8'))


def _poll_job(job_id: str) -> dict:
    last: dict = {}
    for _ in range(POLL_ATTEMPTS):
        last = _request('GET', f'/api/v1/jobs/{job_id}')
        if last.get('status') in {'succeeded', 'failed'}:
            return last
        time.sleep(POLL_INTERVAL)
    return last


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        created = _request(
            'POST',
            '/api/v1/conversation/generate',
            {
                'script': [
                    {'speaker': 'A', 'text': 'Hello there.'},
                    {'speaker': 'B', 'text': 'Welcome back.'},
                ],
                'speaker_voice_map': {'A': None, 'B': None},
                'provider_strategy': 'per_voice',
                'merge_output': True,
            },
        )
        job = _poll_job(created['job_id'])
        artifacts = (job.get('runtime_json') or {}).get('artifacts') or []
        report = {
            'success': job.get('status') == 'succeeded' and bool(artifacts),
            'job': job,
            'artifact_count': len(artifacts),
        }
    except (HTTPError, URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
        report = {'success': False, 'error': str(exc)}

    out = REPORT_DIR / 'e2e_conversation.json'
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'[e2e-conversation] wrote {out}')
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
