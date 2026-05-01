from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from app.services.feature_execution_guard import assert_capability_ready, not_implemented
from app.services.stt_service import STTService

router = APIRouter(prefix="/transcription", tags=["Transcription"])


class TranscriptionRequest(BaseModel):
    artifact_id: str | None = None
    audio_path: str | None = None
    language: str = "auto"
    export_formats: list[str] = ["json", "srt", "vtt"]


@router.post("/transcribe")
def transcribe(payload: TranscriptionRequest):
    state = assert_capability_ready("stt")
    if not payload.artifact_id and not payload.audio_path:
        raise HTTPException(status_code=422, detail={"error": "artifact_id_or_audio_path_required"})
    try:
        return STTService().transcribe(payload.model_dump())
    except NotImplementedError:
        not_implemented("stt", state.provider, "STT service is not wired to artifact storage or provider adapter.")
