from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Header, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.audio_factory.task_mapper import build_clone_preview_task
from app.core.storage import StorageService
from app.schemas.job import JobStatusOut
from app.schemas.voice_clone import VoiceCloneCreateRequest, VoiceCloneUploadResponse, VoiceClonePreviewRequest
from app.services.voice_clone_service import VoiceCloneService

router = APIRouter()

MAX_CLONE_SAMPLE_BYTES = 20 * 1024 * 1024
ALLOWED_CLONE_SAMPLE_SUFFIXES = {'.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg'}


@router.post('/upload', response_model=VoiceCloneUploadResponse)
async def upload_clone_sample(file: UploadFile = File(...)) -> VoiceCloneUploadResponse:
    content_type = file.content_type or ''
    if not content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail='Chi ho tro tai len tep audio')

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail='Tep tai len rong')
    if len(data) > MAX_CLONE_SAMPLE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail='Tep vuot qua gioi han 20MB')

    suffix = Path(file.filename or '').suffix.lower()
    if suffix and suffix not in ALLOWED_CLONE_SAMPLE_SUFFIXES:
        raise HTTPException(status_code=400, detail='Dinh dang tep audio khong duoc ho tro')

    storage = StorageService()
    key = f"voice-clone/samples/{uuid4().hex}{suffix}"
    stored = storage.put_bytes(key, data, content_type)
    return VoiceCloneUploadResponse(file_id=stored.key, upload_url=stored.public_url)


@router.post('/create', response_model=JobStatusOut)
def create_clone(
    payload: VoiceCloneCreateRequest,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    idempotency_key: str | None = Header(default=None, alias='Idempotency-Key'),
) -> JobStatusOut:
    try:
        return VoiceCloneService(db).submit_clone(payload, user_id=user_id, idempotency_key=idempotency_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post('/{voice_id}/preview', response_model=JobStatusOut)
def preview_clone(
    voice_id: UUID,
    payload: VoiceClonePreviewRequest,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    idempotency_key: str | None = Header(default=None, alias='Idempotency-Key'),
) -> JobStatusOut:
    task = build_clone_preview_task(voice_id, payload)
    return VoiceCloneService(db).submit_preview_task(voice_id, task, user_id=user_id, idempotency_key=idempotency_key)


@router.post('/shift', response_model=JobStatusOut)
async def shift_voice(
    file: UploadFile = File(...),
    pitch_semitones: float = 0,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    idempotency_key: str | None = Header(default=None, alias='Idempotency-Key'),
) -> JobStatusOut:
    """Shift voice pitch by semitones (negative=lower, positive=higher)."""
    content_type = file.content_type or ''
    if not content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail='Chi ho tro tai len tep audio')

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail='Tep tai len rong')
    if len(data) > 50 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail='Tep vuot qua gioi han 50MB')

    storage = StorageService()
    key = f"voice-changer/uploads/{uuid4().hex}"
    stored = storage.put_bytes(key, data, content_type)

    return VoiceCloneService(db).submit_shift_job(
        sample_file_id=stored.key,
        user_id=user_id,
        pitch_semitones=pitch_semitones,
        idempotency_key=idempotency_key,
    )
