from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.job import JobStatusOut
from app.schemas.tts import TTSGenerateRequest, TTSPreviewRequest
from app.services.tts_service import TTSService

router = APIRouter()


@router.post('/generate', response_model=JobStatusOut)
def generate_tts(payload: TTSGenerateRequest, db: Session = Depends(get_db)) -> JobStatusOut:
    return TTSService(db).submit_generate(payload)


@router.post('/preview', response_model=JobStatusOut)
def preview_tts(payload: TTSPreviewRequest, db: Session = Depends(get_db)) -> JobStatusOut:
    return TTSService(db).submit_preview(payload)
