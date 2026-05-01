from pydantic import BaseModel
from fastapi import APIRouter, Depends
from app.core.rate_limit import rate_limit
from app.services.feature_execution_guard import assert_capability_ready, not_implemented
from app.services.voice_conversion_job_service import VoiceConversionJobService

router = APIRouter(prefix="/voice-changer", tags=["Voice Changer"])


class VoiceChangerRequest(BaseModel):
    input_artifact_id: str | None = None
    input_path: str | None = None
    target_voice_id: str
    preserve_formants: bool = True


@router.post("/convert")
def convert_voice(
    payload: VoiceChangerRequest,
    _rl: None = Depends(rate_limit(max_requests=20, window_seconds=60)),
):
    state = assert_capability_ready("voice_changer")
    try:
        return VoiceConversionJobService().convert(payload.model_dump())
    except NotImplementedError:
        not_implemented("voice_changer", state.provider, "Real voice conversion adapter is not wired. Pitch shifting is not production voice conversion.")
