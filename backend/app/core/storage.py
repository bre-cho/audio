from __future__ import annotations

import hashlib
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings


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
    """Storage abstraction with local and S3 backends."""

    def __init__(self, root_dir: str | Path | None = None, public_prefix: str = "/artifacts") -> None:
        self.backend = (settings.storage_backend or "local").lower().strip()
        self.root_dir = Path(root_dir or os.getenv("ARTIFACT_ROOT", "/artifacts"))
        self.public_prefix = public_prefix.rstrip("/")
        self.s3_bucket = settings.s3_bucket
        self.s3_endpoint_url = settings.s3_endpoint_url
        self.s3_region = settings.s3_region
        self.s3_public_base_url = (settings.s3_public_base_url or "").rstrip("/") or None

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

        clean_key = key.lstrip("/")
        if self.backend == "s3":
            return self._put_bytes_s3(clean_key, bytes(data), content_type)
        return self._put_bytes_local(clean_key, bytes(data), content_type)

    def _put_bytes_local(self, clean_key: str, data: bytes, content_type: str) -> StoredObject:
        path = self._resolve_path(clean_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        tmp_path.write_bytes(data)

        expected_size = len(data)
        actual_size = tmp_path.stat().st_size
        if actual_size != expected_size:
            tmp_path.unlink(missing_ok=True)
            raise RuntimeError(f"artifact write size mismatch: expected={expected_size} actual={actual_size}")

        checksum = compute_sha256(data)
        written_checksum = compute_sha256(tmp_path.read_bytes())
        if written_checksum != checksum:
            tmp_path.unlink(missing_ok=True)
            raise RuntimeError("artifact checksum mismatch after write")

        tmp_path.replace(path)

        return StoredObject(
            key=clean_key,
            public_url=f"{self.public_prefix}/{clean_key}",
            path=str(path),
            mime_type=content_type,
            size_bytes=actual_size,
            checksum=checksum,
        )

    def _build_s3_client(self):
        try:
            import boto3
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("S3 backend requires boto3. Add boto3 to requirements.") from exc

        return boto3.client(
            "s3",
            endpoint_url=self.s3_endpoint_url,
            region_name=self.s3_region,
        )

    def _resolve_s3_public_url(self, clean_key: str) -> str | None:
        if self.s3_public_base_url:
            return f"{self.s3_public_base_url}/{clean_key}"
        if self.s3_endpoint_url:
            endpoint = self.s3_endpoint_url.rstrip("/")
            return f"{endpoint}/{self.s3_bucket}/{clean_key}"
        if self.s3_region:
            return f"https://{self.s3_bucket}.s3.{self.s3_region}.amazonaws.com/{clean_key}"
        return f"https://{self.s3_bucket}.s3.amazonaws.com/{clean_key}"

    def _put_bytes_s3(self, clean_key: str, data: bytes, content_type: str) -> StoredObject:
        if not self.s3_bucket:
            raise RuntimeError("S3 backend requires S3_BUCKET to be configured")

        checksum = compute_sha256(data)
        client = self._build_s3_client()
        client.put_object(
            Bucket=self.s3_bucket,
            Key=clean_key,
            Body=data,
            ContentType=content_type,
            Metadata={"sha256": checksum},
        )

        return StoredObject(
            key=clean_key,
            public_url=self._resolve_s3_public_url(clean_key),
            path=f"s3://{self.s3_bucket}/{clean_key}",
            mime_type=content_type,
            size_bytes=len(data),
            checksum=checksum,
        )

    def get_bytes(self, key: str) -> bytes:
        """Read raw bytes from storage. Raises FileNotFoundError if missing."""
        clean_key = key.lstrip("/")
        if self.backend == "s3":
            return self._get_bytes_s3(clean_key)
        return self._get_bytes_local(clean_key)

    def _get_bytes_local(self, clean_key: str) -> bytes:
        path = self._resolve_path(clean_key)
        if not path.exists():
            raise FileNotFoundError(f"Artifact not found: {clean_key}")
        return path.read_bytes()

    def _get_bytes_s3(self, clean_key: str) -> bytes:
        if not self.s3_bucket:
            raise RuntimeError("S3 backend requires S3_BUCKET to be configured")
        client = self._build_s3_client()
        try:
            response = client.get_object(Bucket=self.s3_bucket, Key=clean_key)
            return response["Body"].read()
        except Exception as exc:
            raise FileNotFoundError(f"S3 object not found: {clean_key}") from exc

    def delete(self, key: str) -> bool:
        """Delete an object. Returns True if deleted, False if not found."""
        clean_key = key.lstrip("/")
        if self.backend == "s3":
            return self._delete_s3(clean_key)
        return self._delete_local(clean_key)

    def _delete_local(self, clean_key: str) -> bool:
        path = self._resolve_path(clean_key)
        if not path.exists():
            return False
        path.unlink()
        return True

    def _delete_s3(self, clean_key: str) -> bool:
        if not self.s3_bucket:
            raise RuntimeError("S3 backend requires S3_BUCKET to be configured")
        client = self._build_s3_client()
        client.delete_object(Bucket=self.s3_bucket, Key=clean_key)
        return True
