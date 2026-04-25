from __future__ import annotations

import json
import os
from pathlib import Path


def main() -> int:
    report_dir = Path(os.environ.get('REPORT_DIR', '.audio_factory_report'))
    report_dir.mkdir(parents=True, exist_ok=True)

    reports = []
    for path in sorted(report_dir.glob('*.json')):
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
            reports.append({'file': path.name, 'payload': payload})
        except Exception as exc:
            reports.append({'file': path.name, 'error': str(exc)})

    merged = {
        'factory': 'audio',
        'status': 'failed' if any(item.get('payload', {}).get('success') is False for item in reports if isinstance(item, dict)) else 'passed',
        'reports': reports,
    }

    out = report_dir / 'audio_factory_summary.json'
    out.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'[factory-report] wrote {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
