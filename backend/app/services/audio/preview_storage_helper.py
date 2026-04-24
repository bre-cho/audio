from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.services.object_storage import upload_file_to_object_storage


def persist_audio_preview(*, audio_bytes: bytes, suffix: str = ".mp3") -> tuple[str, str | None]:
    preview_dir = Path(settings.audio_preview_dir)
    preview_dir.mkdir(parents=True, exist_ok=True)
    filename = f"preview_{uuid4()}{suffix}"
    local_path = preview_dir / filename
    local_path.write_bytes(audio_bytes)

    if not settings.audio_preview_upload_to_object_storage:
        return str(local_path), None

    storage_key = f"audio/previews/{filename}"
    stored = upload_file_to_object_storage(
        local_path=str(local_path),
        key=storage_key,
        content_type="audio/mpeg",
    )
    return str(local_path), stored.public_url
