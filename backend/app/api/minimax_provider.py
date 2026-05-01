from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.providers.minimax_provider import MinimaxProvider
from app.services.minimax_capability_service import get_minimax_capabilities

router = APIRouter(prefix="/providers/minimax", tags=["providers:minimax"])


class MinimaxTTSPayload(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    voice_id: str | None = None
    model: str | None = None
    audio_format: str = "mp3"
    speed: float = 1.0
    volume: float = 1.0
    pitch: int = 0


class MinimaxAsyncTTSPayload(BaseModel):
    text: str = Field(min_length=1)
    voice_id: str | None = None
    model: str | None = None
    audio_format: str = "mp3"


class MinimaxVoiceDesignPayload(BaseModel):
    prompt: str = Field(min_length=4, max_length=1000)
    model: str | None = None


@router.get("/health")
def health(settings: Settings = Depends(get_settings)):
    if not settings.minimax_api_key:
        return {"provider": "minimax", "ok": False, "status": "blocked", "reason": "missing_api_key"}
    result = MinimaxProvider(settings).health_check()
    return result.__dict__


@router.get("/capabilities")
def capabilities(settings: Settings = Depends(get_settings)):
    return [item.__dict__ for item in get_minimax_capabilities(settings)]


@router.get("/voices")
def voices(voice_type: str = "all", settings: Settings = Depends(get_settings)):
    try:
        return MinimaxProvider(settings).list_voices(voice_type=voice_type)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/tts/smoke")
def tts_smoke(payload: MinimaxTTSPayload, settings: Settings = Depends(get_settings)):
    try:
        result = MinimaxProvider(settings).synthesize_speech(**payload.model_dump())
        return {
            "provider": result.provider,
            "model": result.model,
            "voice_id": result.voice_id,
            "format": result.audio_format,
            "bytes": len(result.audio_bytes),
            "ok": len(result.audio_bytes) > 0,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/tts/async")
def async_tts(payload: MinimaxAsyncTTSPayload, settings: Settings = Depends(get_settings)):
    try:
        result = MinimaxProvider(settings).create_async_tts_task(**payload.model_dump())
        return result.__dict__
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/tts/async/{task_id}")
def async_tts_status(task_id: str, settings: Settings = Depends(get_settings)):
    try:
        result = MinimaxProvider(settings).query_async_tts_task(task_id)
        return result.__dict__
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/voice-design")
def voice_design(payload: MinimaxVoiceDesignPayload, settings: Settings = Depends(get_settings)):
    try:
        result = MinimaxProvider(settings).design_voice(prompt=payload.prompt, model=payload.model)
        return {
            "provider": "minimax",
            "voice_id": result.voice_id,
            "trial_audio_bytes": len(result.trial_audio_bytes or b""),
            "raw": result.raw,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
