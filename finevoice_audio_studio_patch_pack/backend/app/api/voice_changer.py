from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from app.services.provider_capability_registry import default_registry

router = APIRouter(prefix="/api/voice-changer", tags=["Voice Changer"])


class VoiceChangerRequest(BaseModel):
    input_artifact_id: str
    target_voice_id: str
    provider: str = "local_dsp"
    preserve_formants: bool = True


@router.post("/convert")
def convert_voice(payload: VoiceChangerRequest):
    cap = default_registry().get(payload.provider, "voice_changer")
    if cap.status != "ready":
        raise HTTPException(status_code=409, detail={"status": cap.status, "reason": cap.reason})
    return {"status": "queued", "input_artifact_id": payload.input_artifact_id}
