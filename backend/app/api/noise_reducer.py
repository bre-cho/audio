from __future__ import annotations

import base64
from pathlib import Path
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.audio_engines.noise_reducer.noise_pipeline import reduce_noise_wav
from app.core.storage import StorageService
from app.services.audio_quality.audio_signal_validator import validate_wav_signal

router = APIRouter(prefix='/noise-reducer')
_storage = StorageService()


class NoiseReduceRequest(BaseModel):
    storage_key: str | None = Field(None, description="Storage key of the input WAV artifact")
    audio_b64: str | None = Field(None, description="Base64 WAV input (alternative to storage_key)")
    strength: float = Field(0.65, ge=0.0, le=1.0, description="Noise reduction strength (0–1)")
    noise_profile_ms: int = Field(300, ge=50, le=2000, description="Duration of leading silence used to profile noise floor")
    voice_profile: str = Field("balanced", description="Voice profile: balanced | narration | podcast | livestream")


@router.get('/status')
def noise_reducer_status() -> dict:
    return {
        'feature': 'noise_reducer',
        'feature_status': 'active',
        'algorithm': 'frame_rms_gate',
        'note': 'Spectral noise gate — pure Python, no external deps',
    }


@router.post('/process')
def process_noise_reduction(req: NoiseReduceRequest) -> dict:
    """Load a WAV from storage or base64, denoise it, write back as a new artifact."""
    if req.storage_key:
        try:
            src_path = _storage._resolve_path(req.storage_key)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not src_path.exists():
            raise HTTPException(status_code=404, detail=f"artifact not found: {req.storage_key}")
        input_wav = src_path.read_bytes()
        source_stem = Path(req.storage_key).stem
    elif req.audio_b64:
        try:
            input_wav = base64.b64decode(req.audio_b64)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="invalid base64 audio payload") from exc
        source_stem = f"inline_{uuid.uuid4().hex[:8]}"
    else:
        raise HTTPException(status_code=400, detail="must provide storage_key or audio_b64")

    # Validate input
    sig = validate_wav_signal(input_wav)
    if not sig.passed:
        raise HTTPException(status_code=422, detail=f"invalid input signal: {sig.reason}")

    # Process
    try:
        output_wav, report = reduce_noise_wav(
            input_wav=input_wav,
            strength=req.strength,
            noise_profile_ms=req.noise_profile_ms,
            voice_profile=req.voice_profile,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"noise reduction failed: {exc}") from exc

    # Store output under derived key
    out_key = f"audio/noise_reduced/{source_stem}_denoised.wav"
    stored = _storage.put_bytes(out_key, output_wav, "audio/wav")

    return {
        "status": "ok",
        "output_key": stored.key,
        "public_url": stored.public_url,
        "checksum": stored.checksum,
        "size_bytes": stored.size_bytes,
        "noise_report": report,
    }
