from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'backend'
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.db.session import SessionLocal
from app.models.audio_output import AudioOutput


def main() -> int:
    db = SessionLocal()
    try:
        rows = db.query(AudioOutput).all()
        if not rows:
            print('[artifact-checksum-verify] FAIL: no audio_outputs rows found')
            return 1

        failed: list[tuple[str | None, str]] = []
        for row in rows:
            artifact_id = row.artifact_id or str(row.id)
            if not row.checksum:
                failed.append((artifact_id, 'missing checksum'))
            if not row.size_bytes or row.size_bytes <= 0:
                failed.append((artifact_id, 'invalid size_bytes'))
            if not row.storage_key:
                failed.append((artifact_id, 'missing storage_key'))
            if not row.mime_type:
                failed.append((artifact_id, 'missing mime_type'))
            if row.promotion_status not in {'contract_verified', 'persisted'}:
                failed.append((artifact_id, f'invalid promotion_status={row.promotion_status}'))

        if failed:
            print('[artifact-checksum-verify] FAIL')
            for item in failed:
                print(item)
            return 1

        print(f'[artifact-checksum-verify] PASS: checked {len(rows)} audio_outputs')
        return 0
    finally:
        db.close()


if __name__ == '__main__':
    raise SystemExit(main())
