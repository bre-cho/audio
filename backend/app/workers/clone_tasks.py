from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from app.db.session import SessionLocal
from app.models.audio_job import AudioJob
from app.models.audio_output import AudioOutput
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


def _persist_audio_outputs(db, *, job_uuid: UUID, artifacts: list[dict]) -> None:
    """Persist clone preview artifact contracts idempotently per job."""
    db.query(AudioOutput).filter(AudioOutput.job_id == job_uuid).delete(synchronize_session=False)
    for artifact in artifacts:
        db.add(
            AudioOutput(
                job_id=job_uuid,
                output_type=artifact["artifact_type"],
                storage_key=artifact.get("storage_key") or artifact.get("path") or artifact["url"],
                public_url=artifact.get("url"),
                mime_type=artifact.get("mime_type"),
                duration_ms=500,
                size_bytes=int(artifact.get("size_bytes") or 0),
                checksum=artifact.get("checksum"),
                waveform_json=artifact,
            )
        )


def _clone_preview_runtime(result: dict) -> dict:
    return {
        "provider": "internal_genvoice",
        "artifact_contract_version": result["artifact_contract_version"],
        "preview_url": result["preview_url"],
        "artifacts": result["artifacts"],
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
        _persist_audio_outputs(db, job_uuid=job_uuid, artifacts=result["artifacts"])
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
        snapshot = _get_job_snapshot(job_id) or {"request_json": {}}
        result = write_clone_preview_artifact(job_id, request_json=snapshot.get("request_json") or {})
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
