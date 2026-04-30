import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.audio_factory.task_mapper import build_audio_narration_task, build_audio_preview_task
from app.models.audio_job import AudioJob
from app.providers.capability_registry import CAPABILITIES, ENGINE_CAPABILITIES
from app.repositories.job_repo import JobRepository
from app.schemas.job import JobStatusOut
from app.schemas.provider import AudioCapabilitiesOut, FeatureCapabilityOut
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


@router.get('/capabilities', response_model=AudioCapabilitiesOut)
def audio_capabilities() -> AudioCapabilitiesOut:
    features = {
        'text_to_speech': ('tts', None),
        'voice_clone': ('voice_clone', None),
        'voice_changer': ('voice_conversion', 'voice_changer'),
        'voice_design': ('voice_design', 'voice_design'),
        'sound_effects': ('sound_effect', 'sound_effects'),
        'noise_reducer': ('noise_reduction', 'noise_reduction'),
        'voice_enhancer': ('voice_enhancement', 'voice_enhancement'),
        'podcast_generator': ('podcast_mix', 'podcast_mix'),
    }
    payload: list[FeatureCapabilityOut] = []
    for feature_name, (provider_capability, engine_key) in features.items():
        provider_hits = [
            provider_code
            for provider_code, caps in CAPABILITIES.items()
            if getattr(caps, provider_capability, False) and caps.production_ready
        ]

        engine_caps = ENGINE_CAPABILITIES.get(engine_key) if engine_key else None
        engine_status = (engine_caps or {}).get('status')
        provider_required = bool((engine_caps or {}).get('provider_required', True)) if engine_caps else True

        if provider_hits:
            status = 'ready'
            reason = None
        elif engine_status == 'active' and not provider_required:
            status = 'ready'
            reason = 'Engine-backed feature available without external provider'
        elif engine_status == 'planned':
            status = 'partial'
            reason = 'Engine roadmap planned but no production-ready provider yet'
        elif engine_status == 'disabled':
            status = 'disabled'
            reason = 'Feature disabled in engine capability registry'
        else:
            status = 'disabled'
            reason = 'No production-ready provider capability'

        payload.append(
            FeatureCapabilityOut(
                feature=feature_name,
                status=status,
                reason=reason,
                providers=provider_hits,
            )
        )
    return AudioCapabilitiesOut(features=payload)


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
def audio_preview(
    payload: AudioPreviewRequest,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias='Idempotency-Key'),
) -> JobStatusOut:
    repo = JobRepository(db)
    default_user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
    task = build_audio_preview_task(
        text=payload.text,
        voice=payload.voice,
        provider=payload.provider,
        voice_id=payload.voice_profile_id,
    )
    job, created = repo.create_or_get(
        user_id=default_user_id,
        job_type='tts_preview',
        workflow_type=task.workflow_type.value,
        request_json=task.request_json,
        idempotency_key=idempotency_key,
    )
    if created:
        enqueue_tts_job(str(job.id))
    return JobStatusOut.model_validate(job)


@router.post('/narration', response_model=JobStatusOut, status_code=202)
def audio_narration(
    payload: AudioNarrationRequest,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias='Idempotency-Key'),
) -> JobStatusOut:
    repo = JobRepository(db)
    default_user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
    task = build_audio_narration_task(
        text=payload.text,
        voice_profile_id=payload.voice_profile_id,
        provider=payload.provider,
        project_id=payload.project_id,
    )
    job, created = repo.create_or_get(
        user_id=default_user_id,
        job_type='narration',
        workflow_type=task.workflow_type.value,
        request_json=task.request_json,
        project_id=uuid.UUID(payload.project_id) if payload.project_id else None,
        idempotency_key=idempotency_key,
    )
    if created:
        enqueue_batch_job(str(job.id))
    return JobStatusOut.model_validate(job)
