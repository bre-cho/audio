from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.audio_factory.task_mapper import build_clone_preview_task
from app.schemas.job import JobStatusOut
from app.schemas.voice_clone import VoiceCloneCreateRequest, VoiceCloneUploadResponse, VoiceClonePreviewRequest
from app.services.voice_clone_service import VoiceCloneService

router = APIRouter()


@router.post('/upload', response_model=VoiceCloneUploadResponse)
def upload_clone_sample() -> VoiceCloneUploadResponse:
    return VoiceCloneUploadResponse(file_id='thay-bang-bo-xu-ly-tai-len', upload_url=None)


@router.post('/create', response_model=JobStatusOut)
def create_clone(
    payload: VoiceCloneCreateRequest,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias='Idempotency-Key'),
) -> JobStatusOut:
    try:
        return VoiceCloneService(db).submit_clone(payload, idempotency_key=idempotency_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post('/{voice_id}/preview', response_model=JobStatusOut)
def preview_clone(
    voice_id: UUID,
    payload: VoiceClonePreviewRequest,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias='Idempotency-Key'),
) -> JobStatusOut:
    task = build_clone_preview_task(voice_id, payload)
    return VoiceCloneService(db).submit_preview_task(voice_id, task, idempotency_key=idempotency_key)
