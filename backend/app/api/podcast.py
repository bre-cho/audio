from __future__ import annotations

import base64
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.audio_engines.podcast.podcast_mixer import MixerSegment, mix_podcast_wav
from app.core.storage import StorageService

router = APIRouter(prefix='/podcast')
_storage = StorageService()


class PodcastSegmentIn(BaseModel):
    storage_key: Optional[str] = Field(None, description="Storage key of a pre-recorded WAV segment")
    audio_b64: Optional[str] = Field(None, description="Base64-encoded WAV bytes (alternative to storage_key)")
    speaker: str = Field("", description="Speaker label for the segment")
    pause_after_ms: int = Field(500, ge=0, le=5000, description="Silence after this segment in ms")


class PodcastMixRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    segments: list[PodcastSegmentIn] = Field(..., min_length=1)
    target_sample_rate: int = Field(44100, description="Output sample rate")
    crossfade_ms: int = Field(30, ge=0, le=200, description="Crossfade between segments in ms")


@router.get('/status')
def podcast_status() -> dict:
    return {
        'feature': 'podcast_generator',
        'feature_status': 'active',
        'note': 'Multi-segment WAV mixer with crossfade and silence padding',
    }


@router.post('/mix')
def mix_podcast_endpoint(req: PodcastMixRequest) -> dict:
    """Combine multiple WAV segments into a single podcast audio file."""
    mixer_segments: list[MixerSegment] = []
    for idx, seg in enumerate(req.segments):
        if seg.storage_key:
            try:
                path = _storage._resolve_path(seg.storage_key)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            if not path.exists():
                raise HTTPException(status_code=404, detail=f"segment {idx} not found: {seg.storage_key}")
            wav_bytes = path.read_bytes()
        elif seg.audio_b64:
            try:
                wav_bytes = base64.b64decode(seg.audio_b64)
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"segment {idx}: invalid base64") from exc
        else:
            raise HTTPException(status_code=400, detail=f"segment {idx}: must provide storage_key or audio_b64")

        mixer_segments.append(MixerSegment(
            audio_wav=wav_bytes,
            speaker=seg.speaker,
            pause_after_ms=seg.pause_after_ms,
        ))

    try:
        output_wav, report = mix_podcast_wav(
            segments=mixer_segments,
            target_rate=req.target_sample_rate,
            crossfade_ms=req.crossfade_ms,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"mix failed: {exc}") from exc

    slug = req.title.lower().replace(" ", "_")[:40]
    out_key = f"audio/podcast/{slug}_{uuid.uuid4().hex[:8]}.wav"
    stored = _storage.put_bytes(out_key, output_wav, "audio/wav")

    return {
        "status": "ok",
        "title": req.title,
        "output_key": stored.key,
        "public_url": stored.public_url,
        "checksum": stored.checksum,
        "size_bytes": stored.size_bytes,
        "mix_report": report,
    }
