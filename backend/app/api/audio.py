import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.audio_job import AudioJob
from app.repositories.job_repo import JobRepository
from app.schemas.job import JobStatusOut
from app.workers.audio_tasks import enqueue_batch_job, enqueue_tts_job

router = APIRouter()


class AudioPreviewRequest(BaseModel):
    text: str
    voice: str = "default"
    voice_profile_id: str | None = None
    provider: str | None = None


class AudioNarrationRequest(BaseModel):
    text: str
    voice_profile_id: str | None = None
    project_id: str | None = None
    provider: str | None = None


@router.get('/health')
def audio_health(db: Session = Depends(get_db)) -> dict:
    now_ts = datetime.now(UTC).timestamp()
    queued = db.query(func.count(AudioJob.id)).filter(AudioJob.status == 'queued').scalar() or 0
    processing = db.query(func.count(AudioJob.id)).filter(AudioJob.status == 'processing').scalar() or 0
    failed = db.query(func.count(AudioJob.id)).filter(AudioJob.status == 'failed').scalar() or 0

    def _last_success(job_type: str) -> float | None:
        row = (
            db.query(func.max(AudioJob.updated_at))
            .filter(AudioJob.job_type == job_type, AudioJob.status.in_(['done', 'succeeded', 'success']))
            .scalar()
        )
        if row is None:
            return None
        return row.replace(tzinfo=UTC).timestamp() if row.tzinfo is None else row.timestamp()

    return {
        'status': 'ok',
        'timestamp': now_ts,
        'synthetic_ready': True,
        'queue_depth': {
            'audio_voice_clone_queue_depth': 0,
            'audio_narration_queue_depth': int(queued),
            'audio_audio_mix_queue_depth': int(processing),
        },
        'jobs': {
            'audio_jobs_stuck_total': int(failed),
        },
        'last_success_timestamps': {
            'audio_preview_last_success_timestamp_seconds': _last_success('tts_preview'),
            'audio_narration_last_success_timestamp_seconds': _last_success('narration'),
            'audio_clone_last_success_timestamp_seconds': _last_success('clone'),
            'audio_clone_preview_last_success_timestamp_seconds': _last_success('clone_preview'),
        },
    }


@router.post('/preview', response_model=JobStatusOut, status_code=201)
def audio_preview(payload: AudioPreviewRequest, db: Session = Depends(get_db)) -> JobStatusOut:
    repo = JobRepository(db)
    default_user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
    job = repo.create(user_id=default_user_id, job_type='tts_preview', request_json=payload.model_dump(mode='json'))
    enqueue_tts_job(str(job.id))
    return JobStatusOut.model_validate(job)


@router.post('/narration', response_model=JobStatusOut, status_code=202)
def audio_narration(payload: AudioNarrationRequest, db: Session = Depends(get_db)) -> JobStatusOut:
    repo = JobRepository(db)
    default_user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
    job = repo.create(user_id=default_user_id, job_type='narration', request_json=payload.model_dump(mode='json'))
    enqueue_batch_job(str(job.id))
    return JobStatusOut.model_validate(job)
