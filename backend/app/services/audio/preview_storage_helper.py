from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.core.storage import StorageService, StoredObject


def upload_file_to_object_storage(*, local_path: str, key: str, content_type: str) -> StoredObject:
    data = Path(local_path).read_bytes()
    svc = StorageService()
    return svc.put_bytes(key, data, content_type)


def persist_audio_preview(*, audio_bytes: bytes, suffix: str = ".mp3") -> tuple[str, str | None]:
    preview_dir = Path(getattr(settings, "audio_preview_dir", "/tmp/audio_previews"))
    preview_dir.mkdir(parents=True, exist_ok=True)
    filename = f"preview_{uuid4()}{suffix}"
    local_path = preview_dir / filename
    local_path.write_bytes(audio_bytes)

    if not getattr(settings, "audio_preview_upload_to_object_storage", False):
        return str(local_path), None

    storage_key = f"audio/previews/{filename}"
    stored = upload_file_to_object_storage(
        local_path=str(local_path),
        key=storage_key,
        content_type="audio/mpeg",
    )
    return str(local_path), stored.public_url
