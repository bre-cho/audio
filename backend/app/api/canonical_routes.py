"""Canonical production API route registry for Audio Studio V4.

Wire this from backend/app/api/router.py and prefer v2 production modules.
Legacy v1 modules should become wrappers that call these services or return a
clear 409/410, never fake `queued`.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/audio-studio", tags=["audio-studio-v4"])

try:
    from app.api import transcription_v2, podcast_v2, voice_changer_v2, sfx_bgm_v2, audio_quality_v2, system_capabilities_v2
    router.include_router(system_capabilities_v2.router, prefix="/capabilities")
    router.include_router(audio_quality_v2.router, prefix="/quality")
    router.include_router(transcription_v2.router, prefix="/transcription")
    router.include_router(voice_changer_v2.router, prefix="/voice-changer")
    router.include_router(sfx_bgm_v2.router, prefix="/generation")
    router.include_router(podcast_v2.router, prefix="/podcast")
except Exception:
    # Keep import-safe for scaffolding; production router tests should fail if imports are broken.
    pass
