from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'backend'
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.audio_factory.schema_guard import SchemaGuardError, SchemaGuardService
from app.db.session import engine


def main() -> int:
    try:
        SchemaGuardService(engine).assert_audio_factory_schema()
        print('[schema-guard] PASS: audio factory schema is valid')
        return 0
    except SchemaGuardError as exc:
        print(f'[schema-guard] FAIL: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
