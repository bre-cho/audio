"""Backward-compatibility stub. Use app.core.storage directly."""
from app.core.storage import StorageService, StoredObject


def upload_file_to_object_storage(*, local_path: str, key: str, content_type: str) -> StoredObject:
    from pathlib import Path

    data = Path(local_path).read_bytes()
    svc = StorageService()
    return svc.put_bytes(key, data, content_type)
