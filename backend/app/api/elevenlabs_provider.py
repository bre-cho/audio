from fastapi import APIRouter, HTTPException
from app.providers.elevenlabs import ElevenLabsProvider

router = APIRouter(prefix="/providers/elevenlabs", tags=["providers:elevenlabs"])

@router.get("/health")
def elevenlabs_health():
    provider = ElevenLabsProvider()
    return provider.health_check().__dict__

@router.get("/voices")
def elevenlabs_voices():
    provider = ElevenLabsProvider()
    health = provider.health_check()
    if health.status != "ok":
        raise HTTPException(status_code=409, detail=health.message)
    return {"voices": provider.list_voices()}

@router.get("/usage")
def elevenlabs_usage():
    provider = ElevenLabsProvider()
    try:
        return provider.get_usage()
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
