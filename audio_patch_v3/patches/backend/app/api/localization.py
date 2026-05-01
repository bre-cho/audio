from pydantic import BaseModel
from fastapi import APIRouter
from app.services.feature_execution_guard import assert_capability_ready, not_implemented
from app.services.voice_translate_service import VoiceTranslateService

router = APIRouter(prefix="/localization", tags=["Localization"])


class VoiceTranslateRequest(BaseModel):
    source_artifact_id: str
    target_language: str
    preserve_voice: bool = True


@router.post("/voice-translate")
def voice_translate(payload: VoiceTranslateRequest):
    state = assert_capability_ready("voice_translation")
    try:
        return VoiceTranslateService().translate(payload.model_dump())
    except NotImplementedError:
        not_implemented("voice_translation", state.provider, "Voice translation provider is not wired.")
