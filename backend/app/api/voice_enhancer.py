from __future__ import annotations

import base64
from pathlib import Path
from typing import Literal
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.audio_engines.enhancer.enhancement_pipeline import PRESETS, enhance_voice_wav
from app.core.storage import StorageService
from app.services.audio_quality.audio_signal_validator import validate_wav_signal

router = APIRouter(prefix='/voice-enhancer')
_storage = StorageService()

PresetName = Literal["clean", "broadcast", "podcast"]


class VoiceEnhanceRequest(BaseModel):
    storage_key: str | None = Field(None, description="Storage key of the input WAV artifact")
    audio_b64: str | None = Field(None, description="Base64 WAV input (alternative to storage_key)")
    preset: PresetName = Field("clean", description="Enhancement preset: clean | broadcast | podcast")
    voice_profile: str = Field("balanced", description="Voice profile: balanced | warm | bright | broadcast")


@router.get('/status')
def voice_enhancer_status() -> dict:
    return {
        'feature': 'voice_enhancer',
        'feature_status': 'active',
        'presets': list(PRESETS.keys()),
        'stages': {k: v for k, v in PRESETS.items()},
    }


@router.post('/process')
def process_voice_enhancement(req: VoiceEnhanceRequest) -> dict:
    """Load a WAV from storage or base64, enhance it, and write a new artifact."""
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

    sig = validate_wav_signal(input_wav)
    if not sig.passed:
        raise HTTPException(status_code=422, detail=f"invalid input signal: {sig.reason}")

    try:
        output_wav, report = enhance_voice_wav(
            input_wav=input_wav,
            preset=req.preset,
            voice_profile=req.voice_profile,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"enhancement failed: {exc}") from exc

    out_key = f"audio/enhanced/{source_stem}_{req.preset}.wav"
    stored = _storage.put_bytes(out_key, output_wav, "audio/wav")

    return {
        "status": "ok",
        "output_key": stored.key,
        "public_url": stored.public_url,
        "checksum": stored.checksum,
        "size_bytes": stored.size_bytes,
        "enhancement_report": report,
    }
