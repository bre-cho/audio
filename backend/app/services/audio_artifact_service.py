from __future__ import annotations

import json
import platform
import sys
import uuid
import wave
from datetime import UTC, datetime
from typing import Any

from app.core.storage import StorageService, compute_sha256

DEFAULT_PROVIDER = "internal_genvoice"
DEFAULT_TEMPLATE_VERSION = "audio-placeholder-v1"
DEFAULT_MODEL_VERSION = "internal_genvoice/silent-wav-v1"
DEFAULT_RUNTIME_VERSION = f"python-{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}-{platform.system().lower()}"
ARTIFACT_CONTRACT_VERSION = "v2.truthful-contract"


def sha256_bytes(data: bytes) -> str:
    return compute_sha256(data)


def stable_input_hash(payload: dict[str, Any] | None) -> str:
    """Create a deterministic hash for the job input payload."""
    encoded = json.dumps(payload or {}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(encoded)


def _silent_wav_bytes(duration_seconds: float = 0.5) -> bytes:
    """Build a minimal silent WAV in memory so checksum/size are exact."""
    import io

    sample_rate = 16000
    frames = int(sample_rate * duration_seconds)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * frames)
    return buffer.getvalue()


def _artifact_contract(
    *,
    job_id: str,
    output_type: str,
    stored_key: str,
    path: str,
    public_url: str,
    mime_type: str,
    size_bytes: int,
    checksum: str,
    request_json: dict[str, Any] | None = None,
    provider: str = DEFAULT_PROVIDER,
    template_version: str = DEFAULT_TEMPLATE_VERSION,
    model_version: str = DEFAULT_MODEL_VERSION,
    runtime_version: str = DEFAULT_RUNTIME_VERSION,
    parent_artifact_id: str | None = None,
) -> dict[str, Any]:
    input_hash = stable_input_hash(request_json)
    artifact_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"audio-artifact:{job_id}:{output_type}:{input_hash}:{checksum}"))
    checked_at = datetime.now(UTC).isoformat()
    return {
        "artifact_id": artifact_id,
        "artifact_type": output_type,
        "storage_key": stored_key,
        "path": path,
        "url": public_url,
        "mime_type": mime_type,
        "size_bytes": size_bytes,
        "checksum": checksum,
        "created_at": checked_at,
        "source_job_id": job_id,
        "job_id": job_id,
        "input_hash": input_hash,
        "provider": provider,
        "model_version": model_version,
        "template_version": template_version,
        "runtime_version": runtime_version,
        "parent_artifact_id": parent_artifact_id,
        "write_integrity_pass": True,
        "contract_pass": True,
        "lineage_pass": True,
        # Truthful governance flags: these are not proven by write-time checks.
        "replayability_pass": False,
        "determinism_pass": False,
        "drift_budget_pass": False,
        "replayability_status": "pending",
        "determinism_status": "pending",
        "drift_budget_status": "pending",
        "promotion_status": "contract_verified",
        "promotion_reason": "artifact passed write-time storage integrity and contract validation; replay/determinism/drift gates are pending",
        "checked_at": checked_at,
        "artifact_contract_version": ARTIFACT_CONTRACT_VERSION,
    }


def _create_artifact(
    *,
    job_id: str,
    suffix: str,
    output_type: str,
    request_json: dict[str, Any] | None,
    duration_seconds: float = 0.5,
    storage: StorageService | None = None,
) -> dict[str, Any]:
    filename = f"{job_id}.{suffix}.wav" if suffix else f"{job_id}.wav"
    storage_key = f"audio/{filename}"
    data = _silent_wav_bytes(duration_seconds)
    stored = (storage or StorageService()).put_bytes(storage_key, data, "audio/wav")
    if stored.size_bytes is None or stored.size_bytes <= 0:
        raise RuntimeError("stored artifact has invalid size")
    if not stored.checksum or len(stored.checksum) != 64:
        raise RuntimeError("stored artifact has invalid checksum")
    return _artifact_contract(
        job_id=job_id,
        output_type=output_type,
        stored_key=stored.key,
        path=stored.path or "",
        public_url=stored.public_url or f"/artifacts/{storage_key}",
        mime_type=stored.mime_type or "audio/wav",
        size_bytes=stored.size_bytes,
        checksum=stored.checksum,
        request_json=request_json,
    )


def write_audio_artifacts(job_id: str, request_json: dict[str, Any] | None = None) -> dict[str, Any]:
    """Write audio files and return URLs plus truthful artifact contracts."""
    storage = StorageService()
    preview = _create_artifact(job_id=job_id, suffix="preview", output_type="preview", request_json=request_json, storage=storage)
    output = _create_artifact(job_id=job_id, suffix="", output_type="output", request_json=request_json, storage=storage)
    return {
        "preview_url": preview["url"],
        "output_url": output["url"],
        "artifacts": [preview, output],
        "artifact_contract_version": ARTIFACT_CONTRACT_VERSION,
    }


def write_clone_preview_artifact(job_id: str, request_json: dict[str, Any] | None = None) -> str:
    artifact = _create_artifact(
        job_id=job_id,
        suffix="clone_preview",
        output_type="clone_preview",
        request_json=request_json,
    )
    return artifact["url"]
