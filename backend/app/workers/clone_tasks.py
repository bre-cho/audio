from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from app.audio_factory import AudioFactoryExecutor, AudioTaskRequest, AudioWorkflowType
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
            "request_json": job.request_json or {},
            "runtime_json": job.runtime_json or {},
        }
    finally:
        db.close()


def _build_clone_preview_task(job_id: str, snapshot: dict | None) -> AudioTaskRequest:
    payload = (snapshot or {}).get("request_json") or {}
    return AudioTaskRequest(
        workflow_type=AudioWorkflowType.CLONE_PREVIEW,
        source_job_id=job_id,
        request_json=payload,
        text=payload.get("text"),
        clone_source_key=payload.get("clone_source_key") or payload.get("sample_file_id"),
        provider=payload.get("provider") or "internal_genvoice",
        metadata={"job_type": (snapshot or {}).get("job_type")},
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


def _clone_preview_runtime(result: dict) -> dict:
    return {
        "provider": "internal_genvoice",
        "artifact_contract_version": result["artifact_contract_version"],
        "preview_url": result["preview_url"],
        "artifacts": result["artifacts"],
        "factory_validation": result.get("factory_validation", {}),
        "factory_metrics": result.get("factory_metrics", {}),
        "promotion_gate": {
            "contract_pass": True,
            "lineage_pass": True,
            "write_integrity_pass": True,
            "replayability_pass": False,
            "determinism_pass": False,
            "drift_budget_pass": False,
            "replayability_status": "pending",
            "determinism_status": "pending",
            "drift_budget_status": "pending",
            "promotion_status": "contract_verified",
            "promotion_reason": "clone preview artifact passed write-time storage integrity and contract validation; advanced gates pending",
            "checked_at": datetime.now(UTC).isoformat(),
        },
    }


def _mark_clone_preview_succeeded_with_artifacts(job_id: str, *, result: dict) -> None:
    db = SessionLocal()
    try:
        job_uuid = UUID(job_id)
        job = db.query(AudioJob).filter(AudioJob.id == job_uuid).one_or_none()
        if job is None:
            logger.warning("Job %s not found in DB", job_id)
            return
        job.status = "succeeded"
        job.preview_url = result["preview_url"]
        job.runtime_json = _clone_preview_runtime(result)
        job.finished_at = datetime.now(UTC)
        job.updated_at = datetime.now(UTC)
        db.commit()
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
            raise RuntimeError(execution.incident.get("error_message") if execution.incident else execution.validation.get("error"))
        result = {
            "preview_url": execution.preview_url,
            "artifacts": [artifact.model_dump() for artifact in execution.artifacts],
            "artifact_contract_version": execution.artifact_contract_version,
            "factory_validation": execution.validation,
            "factory_metrics": execution.metrics,
        }
        _mark_clone_preview_succeeded_with_artifacts(job_id, result=result)
        return {'job_id': job_id, 'status': 'succeeded', **result}
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
