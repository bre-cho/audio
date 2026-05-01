from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from app.services.provider_capability_registry import default_registry

router = APIRouter(prefix="/transcription", tags=["Transcription"])


class TranscriptionRequest(BaseModel):
    artifact_id: str
    language: str = "auto"
    export_formats: list[str] = ["json", "srt", "vtt"]


@router.post("/transcribe")
def transcribe(payload: TranscriptionRequest, provider: str = "stt_provider"):
    cap = default_registry().get(provider, "stt")
    if cap.status != "ready":
        raise HTTPException(status_code=409, detail={"status": cap.status, "reason": cap.reason})
    return {"status": "queued", "artifact_id": payload.artifact_id}
