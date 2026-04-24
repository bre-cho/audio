from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.db.session import SessionLocal
from app.models.audio_job import AudioJob
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _update_job(job_id: str, **kwargs) -> None:
    db = SessionLocal()
    try:
        job = db.query(AudioJob).filter(AudioJob.id == job_id).one_or_none()
        if job is None:
            logger.warning("Job %s not found in DB", job_id)
            return
        for key, value in kwargs.items():
            setattr(job, key, value)
        job.updated_at = datetime.now(UTC)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def enqueue_tts_job(job_id: str) -> None:
    process_tts_job.delay(job_id)


def enqueue_conversation_job(job_id: str) -> None:
    process_conversation_job.delay(job_id)


def enqueue_batch_job(job_id: str) -> None:
    process_batch_job.delay(job_id)


@celery_app.task(name='audio.process_tts_job', bind=True, max_retries=3)
def process_tts_job(self, job_id: str) -> dict:
    try:
        _update_job(job_id, status='processing', started_at=datetime.now(UTC))
        # Minimal stub: generate silent placeholder bytes and mark succeeded
        audio_bytes = b''
        runtime = {'provider': 'internal', 'audio_bytes_len': len(audio_bytes)}
        _update_job(
            job_id,
            status='succeeded',
            runtime_json=runtime,
            finished_at=datetime.now(UTC),
        )
        return {'job_id': job_id, 'status': 'succeeded'}
    except Exception as exc:
        logger.exception("process_tts_job failed for %s", job_id)
        _update_job(
            job_id,
            status='failed',
            error_code='tts_error',
            error_message=str(exc),
            finished_at=datetime.now(UTC),
        )
        raise self.retry(exc=exc, countdown=10)


@celery_app.task(name='audio.process_conversation_job', bind=True, max_retries=3)
def process_conversation_job(self, job_id: str) -> dict:
    try:
        _update_job(job_id, status='processing', started_at=datetime.now(UTC))
        runtime = {'provider': 'internal'}
        _update_job(
            job_id,
            status='succeeded',
            runtime_json=runtime,
            finished_at=datetime.now(UTC),
        )
        return {'job_id': job_id, 'status': 'succeeded'}
    except Exception as exc:
        logger.exception("process_conversation_job failed for %s", job_id)
        _update_job(
            job_id,
            status='failed',
            error_code='conversation_error',
            error_message=str(exc),
            finished_at=datetime.now(UTC),
        )
        raise self.retry(exc=exc, countdown=10)


@celery_app.task(name='audio.process_batch_job', bind=True, max_retries=3)
def process_batch_job(self, job_id: str) -> dict:
    try:
        _update_job(job_id, status='processing', started_at=datetime.now(UTC))
        runtime = {'provider': 'internal'}
        _update_job(
            job_id,
            status='succeeded',
            runtime_json=runtime,
            finished_at=datetime.now(UTC),
        )
        return {'job_id': job_id, 'status': 'succeeded'}
    except Exception as exc:
        logger.exception("process_batch_job failed for %s", job_id)
        _update_job(
            job_id,
            status='failed',
            error_code='batch_error',
            error_message=str(exc),
            finished_at=datetime.now(UTC),
        )
        raise self.retry(exc=exc, countdown=10)
