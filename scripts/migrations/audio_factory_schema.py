from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
ALEMBIC_INI = BACKEND / "alembic.ini"


def main() -> int:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ALEMBIC_INI), "upgrade", "head"],
        cwd=str(BACKEND),
    )
    if result.returncode != 0:
        print("[audio-factory-migrate] FAIL: alembic upgrade head failed", file=sys.stderr)
        return 1
    print("[audio-factory-migrate] PASS: schema applied via alembic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
