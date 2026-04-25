from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StoredObject:
    key: str
    public_url: str | None = None
    path: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    checksum: str | None = None


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class StorageService:
    """Local artifact storage with atomic write + integrity metadata.

    This keeps the existing public contract (`key`, `public_url`) while making
    the storage layer authoritative for size/checksum/path metadata. S3/GCS can
    later implement the same return contract without changing callers.
    """

    def __init__(self, root_dir: str | Path | None = None, public_prefix: str = "/artifacts") -> None:
        self.root_dir = Path(root_dir or os.getenv("ARTIFACT_ROOT", "/artifacts"))
        self.public_prefix = public_prefix.rstrip("/")

    def _resolve_path(self, key: str) -> Path:
        clean_key = key.lstrip("/")
        target = (self.root_dir / clean_key).resolve()
        root = self.root_dir.resolve()
        if root not in target.parents and target != root:
            raise ValueError(f"storage key escapes artifact root: {key}")
        return target

    def put_bytes(self, key: str, data: bytes, content_type: str) -> StoredObject:
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes")
        if len(data) <= 0:
            raise ValueError("refusing to store empty artifact")

        path = self._resolve_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_name(f".{path.name}.tmp")
        tmp_path.write_bytes(bytes(data))

        expected_size = len(data)
        actual_size = tmp_path.stat().st_size
        if actual_size != expected_size:
            tmp_path.unlink(missing_ok=True)
            raise RuntimeError(f"artifact write size mismatch: expected={expected_size} actual={actual_size}")

        checksum = compute_sha256(bytes(data))
        written_checksum = compute_sha256(tmp_path.read_bytes())
        if written_checksum != checksum:
            tmp_path.unlink(missing_ok=True)
            raise RuntimeError("artifact checksum mismatch after write")

        tmp_path.replace(path)

        return StoredObject(
            key=key.lstrip("/"),
            public_url=f"{self.public_prefix}/{key.lstrip('/')}",
            path=str(path),
            mime_type=content_type,
            size_bytes=actual_size,
            checksum=checksum,
        )
