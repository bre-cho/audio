from __future__ import annotations

import base64
import subprocess
import tempfile
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

_WAV_MAGIC = b"RIFF"

PresetName = Literal["clean", "broadcast", "podcast"]


def _ensure_wav_bytes(data: bytes, source_name: str) -> bytes:
    """Return WAV bytes, decoding via ffmpeg if the input is not PCM WAV."""
    if data[:4] == _WAV_MAGIC:
        return data
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / f"{source_name}.audio"
        dst = Path(tmpdir) / f"{source_name}.wav"
        src.write_bytes(data)
        cmd = [
            "ffmpeg", "-y", "-i", str(src),
            "-ac", "1", "-ar", "44100", "-sample_fmt", "s16",
            str(dst),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0 or not dst.exists() or dst.stat().st_size == 0:
            raise ValueError(
                f"audio_decode_failed: input is not valid WAV/audio — {proc.stderr[-300:]}"
            )
        return dst.read_bytes()


class VoiceEnhanceRequest(BaseModel):
    storage_key: str | None = Field(None, description="Storage key of the input audio artifact (WAV, MP3, FLAC …)")
    audio_b64: str | None = Field(None, description="Base64 audio input (alternative to storage_key)")
    preset: PresetName = Field("clean", description="Enhancement preset: clean | broadcast | podcast")
    voice_profile: str = Field("balanced", description="Voice profile: balanced | warm | bright | broadcast")


@router.get('/status')
def voice_enhancer_status() -> dict:
    return {
        'feature': 'voice_enhancer',
        'feature_status': 'active',
        'presets': list(PRESETS.keys()),
        'stages': {k: v for k, v in PRESETS.items()},
        'note': 'MP3/FLAC auto-decoded via ffmpeg',
    }


@router.post('/process')
def process_voice_enhancement(req: VoiceEnhanceRequest) -> dict:
    """Load audio from storage or base64, enhance it, and write a new artifact.

    Input can be WAV, MP3, FLAC, OGG, or any ffmpeg-supported format.
    Non-WAV files are automatically decoded to 44 100 Hz mono PCM WAV before
    processing and the enhanced output is stored as WAV.
    """
    if req.storage_key:
        try:
            src_path = _storage._resolve_path(req.storage_key)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not src_path.exists():
            raise HTTPException(status_code=404, detail=f"artifact not found: {req.storage_key}")
        raw_bytes = src_path.read_bytes()
        source_stem = Path(req.storage_key).stem
    elif req.audio_b64:
        try:
            raw_bytes = base64.b64decode(req.audio_b64)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="invalid base64 audio payload") from exc
        source_stem = f"inline_{uuid.uuid4().hex[:8]}"
    else:
        raise HTTPException(status_code=400, detail="must provide storage_key or audio_b64")

    # Auto-decode to WAV if needed
    try:
        input_wav = _ensure_wav_bytes(raw_bytes, source_stem)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

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
