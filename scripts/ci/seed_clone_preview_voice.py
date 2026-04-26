from __future__ import annotations

import os
from uuid import UUID

from app.db.session import SessionLocal
from app.models.voice import Voice

VOICE_ID = UUID(os.environ.get("E2E_CLONE_PREVIEW_VOICE_ID", "00000000-0000-0000-0000-000000000123"))


def main() -> int:
    db = SessionLocal()
    try:
        existing = db.get(Voice, VOICE_ID)
        if existing is None:
            db.add(
                Voice(
                    id=VOICE_ID,
                    name="CI Clone Preview Voice",
                    source_type="system",
                    visibility="private",
                    is_active=True,
                    metadata_json={"seeded_by": "scripts/ci/seed_clone_preview_voice.py"},
                )
            )
            db.commit()
            print(f"[seed-clone-preview-voice] created voice_id={VOICE_ID}")
        else:
            print(f"[seed-clone-preview-voice] exists voice_id={VOICE_ID}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
