from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.job import JobStatusOut
from app.schemas.voice_clone import VoiceCloneCreateRequest, VoiceCloneUploadResponse, VoiceClonePreviewRequest
from app.services.voice_clone_service import VoiceCloneService

router = APIRouter()


@router.post('/upload', response_model=VoiceCloneUploadResponse)
def upload_clone_sample() -> VoiceCloneUploadResponse:
    return VoiceCloneUploadResponse(file_id='replace-with-upload-handler', upload_url=None)


@router.post('/create', response_model=JobStatusOut)
def create_clone(payload: VoiceCloneCreateRequest, db: Session = Depends(get_db)) -> JobStatusOut:
    return VoiceCloneService(db).submit_clone(payload)


@router.post('/{voice_id}/preview', response_model=JobStatusOut)
def preview_clone(voice_id: UUID, payload: VoiceClonePreviewRequest, db: Session = Depends(get_db)) -> JobStatusOut:
    return VoiceCloneService(db).submit_preview(voice_id, payload)
