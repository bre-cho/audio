from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from app.audio_factory import AudioFactoryExecutor, AudioJobFinalizer, AudioTaskRequest, AudioWorkflowType
from app.db.session import SessionLocal
from app.models.audio_job import AudioJob
from app.services.audio_artifact_service import write_clone_preview_artifact
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


class _ClonePreviewRuntime:
    def run(self, task: AudioTaskRequest, workflow_spec: dict) -> dict:
        del workflow_spec
        return write_clone_preview_artifact(task.source_job_id or "", request_json=task.request_json)


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


def _get_job_snapshot(job_id: str) -> dict | None:
    db = SessionLocal()
    try:
        job_uuid = UUID(job_id)
        job = db.query(AudioJob).filter(AudioJob.id == job_uuid).one_or_none()
        if job is None:
            return None
        return {
            "id": str(job.id),
            "job_type": job.job_type,
            "workflow_type": job.workflow_type,
            "request_json": job.request_json or {},
            "runtime_json": job.runtime_json or {},
        }
    finally:
        db.close()


def _build_clone_preview_task(job_id: str, snapshot: dict | None) -> AudioTaskRequest:
    payload = (snapshot or {}).get("request_json") or {}
    raw_workflow_type = (snapshot or {}).get("workflow_type")
    workflow_type = AudioWorkflowType(raw_workflow_type) if raw_workflow_type and raw_workflow_type != "unknown" else AudioWorkflowType.CLONE_PREVIEW
    return AudioTaskRequest(
        workflow_type=workflow_type,
        source_job_id=job_id,
        request_json=payload,
        text=payload.get("text"),
        clone_source_key=payload.get("clone_source_key") or payload.get("sample_file_id") or payload.get("voice"),
        provider=payload.get("provider") or "internal_genvoice",
        metadata={
            "job_type": (snapshot or {}).get("job_type"),
            "workflow_type": workflow_type.value,
        },
    )


def _execute_clone_preview(job_id: str):
    snapshot = _get_job_snapshot(job_id) or {"request_json": {}}
    task = _build_clone_preview_task(job_id, snapshot)
    db = SessionLocal()
    try:
        executor = AudioFactoryExecutor(provider_runtime=_ClonePreviewRuntime())
        return executor.execute(db=db, task=task)
    finally:
        db.close()


def _factory_error(execution) -> str:
    if execution.incident:
        return execution.incident.get("error_message") or str(execution.incident)
    return execution.validation.get("error") or str(execution.validation)


def _finalize_clone_preview_success(job_id: str, *, execution) -> dict:
    db = SessionLocal()
    try:
        job = AudioJobFinalizer().finalize_success(
            db=db,
            job_id=job_id,
            execution=execution,
            promotion_reason="clone preview artifact passed factory file validation, DB persistence validation, and finalizer success contract",
        )
        return job.runtime_json
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


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
        execution = _execute_clone_preview(job_id)
        if not execution.success:
            raise RuntimeError(_factory_error(execution))

        runtime_json = _finalize_clone_preview_success(job_id, execution=execution)
        return {'job_id': job_id, 'status': 'succeeded', **runtime_json}
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
