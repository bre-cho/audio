import os
from fastapi import APIRouter
from pydantic import BaseModel

from app.audio_engines.stt.whisper_adapter import WhisperAdapter
from app.services.provider_capability_gate_v2 import require_capability
from app.services.subtitle_export_service_v2 import export_transcript_bundle

router = APIRouter()


class TranscriptionRequest(BaseModel):
    audio_path: str
    output_dir: str = "artifacts/transcripts"


@router.post("/transcribe")
def transcribe_v2(payload: TranscriptionRequest):
    require_capability("stt")
    result = WhisperAdapter(os.getenv("WHISPER_MODEL", "base")).transcribe(payload.audio_path)
    files = export_transcript_bundle(result.dict(), payload.output_dir)
    return {"transcript": result.dict(), "files": files}
