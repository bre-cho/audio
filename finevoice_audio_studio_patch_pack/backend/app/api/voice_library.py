from fastapi import APIRouter
from app.models.voice_model import VoiceProfileCreate
from app.services.voice_library_service import VoiceLibraryService

router = APIRouter(prefix="/api/voice-library", tags=["Voice Library"])
_service = VoiceLibraryService()


@router.get("/voices")
def list_voices():
    return {"items": _service.list()}


@router.post("/voices")
def create_voice(payload: VoiceProfileCreate):
    return _service.create(payload)
