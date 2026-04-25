from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.audio_factory.task_mapper import build_tts_generate_task, build_tts_preview_task
from app.schemas.job import JobStatusOut
from app.schemas.tts import TTSGenerateRequest, TTSPreviewRequest
from app.services.tts_service import TTSService

router = APIRouter()


@router.post('/generate', response_model=JobStatusOut)
def generate_tts(
    payload: TTSGenerateRequest,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias='Idempotency-Key'),
) -> JobStatusOut:
    task = build_tts_generate_task(payload)
    return TTSService(db).submit_generate_task(task, payload, idempotency_key=idempotency_key)


@router.post('/preview', response_model=JobStatusOut)
def preview_tts(
    payload: TTSPreviewRequest,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias='Idempotency-Key'),
) -> JobStatusOut:
    task = build_tts_preview_task(payload)
    return TTSService(db).submit_preview_task(task, payload, idempotency_key=idempotency_key)
