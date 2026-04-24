from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from app.db.session import SessionLocal
from app.models.audio_job import AudioJob
from app.services.audio_artifact_service import write_audio_artifacts
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _update_job(job_id: str, **kwargs) -> None:
    db = SessionLocal()
    try:
        job_uuid = UUID(job_id)
        job = db.query(AudioJob).filter(AudioJob.id == job_uuid).one_or_none()
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


def _should_fail_task(task) -> bool:
    return task.request.retries >= task.max_retries


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
        urls = write_audio_artifacts(job_id)
        _update_job(
            job_id,
            status='succeeded',
            preview_url=urls["preview_url"],
            output_url=urls["output_url"],
            runtime_json={'provider': 'internal_genvoice', **urls},
            finished_at=datetime.now(UTC),
        )
        return {'job_id': job_id, 'status': 'succeeded', **urls}
    except Exception as exc:
        logger.exception("Audio task failed for %s", job_id)
        if _should_fail_task(self):
            _update_job(
                job_id,
                status='failed',
                error_code='audio_task_error',
                error_message=str(exc),
                finished_at=datetime.now(UTC),
            )
        else:
            _update_job(
                job_id,
                status='retrying',
                error_code='audio_task_retrying',
                error_message=str(exc),
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
        logger.exception("Audio task failed for %s", job_id)
        if _should_fail_task(self):
            _update_job(
                job_id,
                status='failed',
                error_code='audio_task_error',
                error_message=str(exc),
                finished_at=datetime.now(UTC),
            )
        else:
            _update_job(
                job_id,
                status='retrying',
                error_code='audio_task_retrying',
                error_message=str(exc),
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
        logger.exception("Audio task failed for %s", job_id)
        if _should_fail_task(self):
            _update_job(
                job_id,
                status='failed',
                error_code='audio_task_error',
                error_message=str(exc),
                finished_at=datetime.now(UTC),
            )
        else:
            _update_job(
                job_id,
                status='retrying',
                error_code='audio_task_retrying',
                error_message=str(exc),
            )
        raise self.retry(exc=exc, countdown=10)
