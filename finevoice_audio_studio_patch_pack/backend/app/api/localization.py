from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from app.services.provider_capability_registry import default_registry

router = APIRouter(prefix="/api/localization", tags=["Localization"])


class VoiceTranslateRequest(BaseModel):
    source_artifact_id: str
    target_language: str
    preserve_voice: bool = True


@router.post("/voice-translate")
def voice_translate(payload: VoiceTranslateRequest, provider: str = "translation_provider"):
    cap = default_registry().get(provider, "voice_translation")
    if cap.status != "ready":
        raise HTTPException(status_code=409, detail={"status": cap.status, "reason": cap.reason})
    return {"status": "queued", "source_artifact_id": payload.source_artifact_id}
