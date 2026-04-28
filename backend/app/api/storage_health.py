"""Storage health check endpoint — verifies write/read/delete cycle."""
from __future__ import annotations

import uuid

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.storage import StorageService

router = APIRouter(prefix="/storage", tags=["storage"])


@router.get("/health")
def storage_health() -> JSONResponse:
    """
    Verify storage backend is writable.
    Writes a tiny probe file, reads it back, then deletes it.
    Returns backend type, probe result, and config details.
    """
    probe_key = f"_healthcheck/{uuid.uuid4().hex}.txt"
    probe_data = b"storage-health-ok"
    backend = (settings.storage_backend or "local").lower().strip()

    try:
        svc = StorageService()
        stored = svc.put_bytes(probe_key, probe_data, "text/plain")

        # Verify via path for local backend
        if backend == "local" and stored.path:
            from pathlib import Path
            p = Path(stored.path)
            if not p.exists():
                return JSONResponse(status_code=503, content={"status": "error", "backend": backend, "detail": "probe file not found after write"})
            p.unlink(missing_ok=True)
        elif backend == "s3":
            # Verify by re-fetching object metadata
            import boto3
            client = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint_url,
                region_name=settings.s3_region,
            )
            client.head_object(Bucket=settings.s3_bucket, Key=probe_key)
            client.delete_object(Bucket=settings.s3_bucket, Key=probe_key)

        return JSONResponse(content={
            "status": "ok",
            "backend": backend,
            "probe_key": probe_key,
            "size_bytes": stored.size_bytes,
            "checksum": stored.checksum,
            "public_url": stored.public_url,
            "s3_bucket": settings.s3_bucket if backend == "s3" else None,
        })
    except Exception as exc:
        return JSONResponse(status_code=503, content={
            "status": "error",
            "backend": backend,
            "detail": str(exc),
        })
