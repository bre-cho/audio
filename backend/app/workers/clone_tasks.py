from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from app.db.session import SessionLocal
from app.models.audio_job import AudioJob
from app.services.audio_artifact_service import write_clone_preview_artifact
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


def enqueue_clone_job(job_id: str) -> None:
    process_clone_job.delay(job_id)


def enqueue_clone_preview_job(job_id: str) -> None:
    process_clone_preview_job.delay(job_id)


@celery_app.task(name='audio.process_clone_job', bind=True, max_retries=3)
def process_clone_job(self, job_id: str) -> dict:
    try:
        _update_job(job_id, status='processing', started_at=datetime.now(UTC))
        voice_profile_id = f"voice_{job_id}"
        runtime = {
            'provider': 'internal_genvoice',
            'voice_profile_id': voice_profile_id,
        }
        _update_job(
            job_id,
            status='succeeded',
            runtime_json=runtime,
            finished_at=datetime.now(UTC),
        )
        return {'job_id': job_id, 'status': 'succeeded', 'voice_profile_id': voice_profile_id}
    except Exception as exc:
        logger.exception("Clone task failed for %s", job_id)
        if self.request.retries >= self.max_retries:
            _update_job(
                job_id,
                status='failed',
                error_code='clone_task_error',
                error_message=str(exc),
                finished_at=datetime.now(UTC),
            )
        else:
            _update_job(
                job_id,
                status='retrying',
                error_code='clone_task_retrying',
                error_message=str(exc),
            )
        raise self.retry(exc=exc, countdown=10)


@celery_app.task(name='audio.process_clone_preview_job', bind=True, max_retries=3)
def process_clone_preview_job(self, job_id: str) -> dict:
    try:
        _update_job(job_id, status='processing', started_at=datetime.now(UTC))
        preview_url = write_clone_preview_artifact(job_id)
        runtime = {
            'provider': 'internal_genvoice',
            'preview_url': preview_url,
        }
        _update_job(
            job_id,
            status='succeeded',
            preview_url=preview_url,
            runtime_json=runtime,
            finished_at=datetime.now(UTC),
        )
        return {'job_id': job_id, 'status': 'succeeded', 'preview_url': preview_url}
    except Exception as exc:
        logger.exception("Clone task failed for %s", job_id)
        if self.request.retries >= self.max_retries:
            _update_job(
                job_id,
                status='failed',
                error_code='clone_task_error',
                error_message=str(exc),
                finished_at=datetime.now(UTC),
            )
        else:
            _update_job(
                job_id,
                status='retrying',
                error_code='clone_task_retrying',
                error_message=str(exc),
            )
        raise self.retry(exc=exc, countdown=10)
