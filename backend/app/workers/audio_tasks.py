from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from app.audio_factory import AudioFactoryExecutor, AudioTaskRequest, AudioWorkflowType
from app.db.session import SessionLocal
from app.models.audio_job import AudioJob
from app.services.audio_artifact_service import write_audio_artifacts
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


class _WorkerAudioRuntime:
    def run(self, task: AudioTaskRequest, workflow_spec: dict) -> dict:
        del workflow_spec
        return write_audio_artifacts(task.source_job_id or "", request_json=task.request_json)


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
            "project_id": str(job.project_id) if job.project_id else None,
            "request_json": job.request_json or {},
            "runtime_json": job.runtime_json or {},
        }
    finally:
        db.close()


def _should_fail_task(task) -> bool:
    return task.request.retries >= task.max_retries


def _build_task_request(job_id: str, snapshot: dict | None, workflow_type: AudioWorkflowType) -> AudioTaskRequest:
    payload = (snapshot or {}).get("request_json") or {}
    voice_id = payload.get("voice_id") or payload.get("voice")
    return AudioTaskRequest(
        workflow_type=workflow_type,
        source_job_id=job_id,
        request_json=payload,
        text=payload.get("text"),
        script=payload.get("raw_script") or payload.get("script"),
        conversation_turns=payload.get("conversation_turns") or payload.get("script"),
        voice_id=str(voice_id) if voice_id is not None else None,
        provider=payload.get("provider") or "internal_genvoice",
        model_version=payload.get("model"),
        metadata={"job_type": (snapshot or {}).get("job_type")},
    )


def _execute_factory(job_id: str, workflow_type: AudioWorkflowType) -> tuple[dict | None, object]:
    snapshot = _get_job_snapshot(job_id) or {"request_json": {}}
    task = _build_task_request(job_id, snapshot, workflow_type)
    db = SessionLocal()
    try:
        executor = AudioFactoryExecutor(provider_runtime=_WorkerAudioRuntime())
        return snapshot, executor.execute(db=db, task=task)
    finally:
        db.close()


def enqueue_tts_job(job_id: str) -> None:
    process_tts_job.delay(job_id)


def enqueue_conversation_job(job_id: str) -> None:
    process_conversation_job.delay(job_id)


def enqueue_batch_job(job_id: str) -> None:
    process_batch_job.delay(job_id)


def _promotion_gate(result: dict, promotion_reason: str) -> dict:
    return {
        "contract_pass": True,
        "lineage_pass": True,
        "write_integrity_pass": True,
        # Truthful status: not proven in this worker.
        "replayability_pass": False,
        "determinism_pass": False,
        "drift_budget_pass": False,
        "replayability_status": "pending",
        "determinism_status": "pending",
        "drift_budget_status": "pending",
        "promotion_status": "contract_verified",
        "promotion_reason": promotion_reason,
        "checked_at": datetime.now(UTC).isoformat(),
    }


def _success_runtime(result: dict, promotion_reason: str) -> dict:
    return {
        "provider": "internal_genvoice",
        "artifact_contract_version": result["artifact_contract_version"],
        "artifacts": result["artifacts"],
        "factory_validation": result.get("factory_validation", {}),
        "factory_metrics": result.get("factory_metrics", {}),
        "promotion_gate": _promotion_gate(result, promotion_reason),
        "preview_url": result["preview_url"],
        "output_url": result["output_url"],
    }


def _mark_job_succeeded_with_artifacts(job_id: str, *, result: dict, promotion_reason: str) -> None:
    db = SessionLocal()
    try:
        job_uuid = UUID(job_id)
        job = db.query(AudioJob).filter(AudioJob.id == job_uuid).one_or_none()
        if job is None:
            logger.warning("Job %s not found in DB", job_id)
            return

        job.status = "succeeded"
        job.preview_url = result["preview_url"]
        job.output_url = result["output_url"]
        job.runtime_json = _success_runtime(result, promotion_reason)
        job.finished_at = datetime.now(UTC)
        job.updated_at = datetime.now(UTC)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name="audio.process_tts_job", bind=True, max_retries=3)
def process_tts_job(self, job_id: str) -> dict:
    try:
        _update_job(job_id, status="processing", started_at=datetime.now(UTC))
        _, execution = _execute_factory(job_id, AudioWorkflowType.TTS_PREVIEW)
        if not execution.success:
            raise RuntimeError(execution.incident.get("error_message") if execution.incident else execution.validation.get("error"))
        result = {
            "preview_url": execution.preview_url,
            "output_url": execution.output_url,
            "artifacts": [artifact.model_dump() for artifact in execution.artifacts],
            "artifact_contract_version": execution.artifact_contract_version,
            "factory_validation": execution.validation,
            "factory_metrics": execution.metrics,
        }
        _mark_job_succeeded_with_artifacts(
            job_id,
            result=result,
            promotion_reason="artifacts passed write-time storage integrity and contract validation; advanced gates pending",
        )
        return {"job_id": job_id, "status": "succeeded", **result}
    except Exception as exc:
        logger.exception("Audio task failed for %s", job_id)
        if _should_fail_task(self):
            _update_job(job_id, status="failed", error_code="audio_task_error", error_message=str(exc), finished_at=datetime.now(UTC))
        else:
            _update_job(job_id, status="retrying", error_code="audio_task_retrying", error_message=str(exc))
        raise self.retry(exc=exc, countdown=10)


@celery_app.task(name="audio.process_conversation_job", bind=True, max_retries=3)
def process_conversation_job(self, job_id: str) -> dict:
    try:
        _update_job(job_id, status="processing", started_at=datetime.now(UTC))
        _, execution = _execute_factory(job_id, AudioWorkflowType.CONVERSATION)
        if not execution.success:
            raise RuntimeError(execution.incident.get("error_message") if execution.incident else execution.validation.get("error"))
        result = {
            "preview_url": execution.preview_url,
            "output_url": execution.output_url,
            "artifacts": [artifact.model_dump() for artifact in execution.artifacts],
            "artifact_contract_version": execution.artifact_contract_version,
            "factory_validation": execution.validation,
            "factory_metrics": execution.metrics,
        }
        _mark_job_succeeded_with_artifacts(
            job_id,
            result=result,
            promotion_reason="conversation artifacts passed write-time storage integrity and contract validation; advanced gates pending",
        )
        return {"job_id": job_id, "status": "succeeded", **result}
    except Exception as exc:
        logger.exception("Audio task failed for %s", job_id)
        if _should_fail_task(self):
            _update_job(job_id, status="failed", error_code="audio_task_error", error_message=str(exc), finished_at=datetime.now(UTC))
        else:
            _update_job(job_id, status="retrying", error_code="audio_task_retrying", error_message=str(exc))
        raise self.retry(exc=exc, countdown=10)


@celery_app.task(name="audio.process_batch_job", bind=True, max_retries=3)
def process_batch_job(self, job_id: str) -> dict:
    try:
        _update_job(job_id, status="processing", started_at=datetime.now(UTC))
        _, execution = _execute_factory(job_id, AudioWorkflowType.NARRATION)
        if not execution.success:
            raise RuntimeError(execution.incident.get("error_message") if execution.incident else execution.validation.get("error"))
        result = {
            "preview_url": execution.preview_url,
            "output_url": execution.output_url,
            "artifacts": [artifact.model_dump() for artifact in execution.artifacts],
            "artifact_contract_version": execution.artifact_contract_version,
            "factory_validation": execution.validation,
            "factory_metrics": execution.metrics,
        }
        _mark_job_succeeded_with_artifacts(
            job_id,
            result=result,
            promotion_reason="narration artifacts passed write-time storage integrity and contract validation; advanced gates pending",
        )
        return {"job_id": job_id, "status": "succeeded", **result}
    except Exception as exc:
        logger.exception("Audio task failed for %s", job_id)
        if _should_fail_task(self):
            _update_job(job_id, status="failed", error_code="audio_task_error", error_message=str(exc), finished_at=datetime.now(UTC))
        else:
            _update_job(job_id, status="retrying", error_code="audio_task_retrying", error_message=str(exc))
        raise self.retry(exc=exc, countdown=10)
