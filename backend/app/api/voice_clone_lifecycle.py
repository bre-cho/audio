from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from app.services.voice_clone_lifecycle_service import VoiceCloneLifecycleService

router = APIRouter(prefix="/voice-clone-lifecycle", tags=["Voice Clone Lifecycle"])


class CloneCreateRequest(BaseModel):
    name: str
    sample_paths: list[str]
    description: str | None = None
    consent_proof_id: str


@router.post("/create")
def create_clone(payload: CloneCreateRequest):
    try:
        return VoiceCloneLifecycleService().create_clone(**payload.model_dump())
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/{external_voice_id}/status")
def clone_status(external_voice_id: str):
    return VoiceCloneLifecycleService().poll_status(external_voice_id)
