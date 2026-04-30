from __future__ import annotations

import asyncio
import logging
import mimetypes
from datetime import UTC, datetime
from uuid import UUID

from app.audio_factory import AudioFactoryExecutor, AudioJobFinalizer, AudioTaskRequest, AudioWorkflowType
from app.core.runtime_guard import RuntimeGuardError, assert_real_provider
from app.core.storage import StorageService
from app.db.session import SessionLocal
from app.models.audio_job import AudioJob
from app.models.voice import Voice
from app.services.audio_artifact_service import write_clone_preview_artifact
from app.services.audio_provider_router import get_audio_provider_adapter, resolve_audio_provider
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


class _ClonePreviewRuntime:
    def run(self, task: AudioTaskRequest, workflow_spec: dict) -> dict:
        del workflow_spec
        provider = resolve_audio_provider(
            requested_provider=task.provider,
            default_provider="internal_genvoice",
        )
        assert_real_provider(provider, feature=task.workflow_type.value)
        return write_clone_preview_artifact(
            task.source_job_id or "",
            request_json=task.request_json,
            provider=provider,
        )


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
            "user_id": str(job.user_id),
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


def _finalize_clone_preview_success(job_id: str, *, execution, provider: str) -> dict:
    db = SessionLocal()
    try:
        job = AudioJobFinalizer().finalize_success(
            db=db,
            job_id=job_id,
            execution=execution,
            promotion_reason="clone preview artifact passed factory file validation, DB persistence validation, and finalizer success contract",
            provider=provider,
        )
        return job.runtime_json
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _is_permanent_clone_error(exc: Exception) -> bool:
    return isinstance(exc, (ValueError, FileNotFoundError, RuntimeGuardError, NotImplementedError))


def _execute_clone_job(job_id: str) -> dict:
    snapshot = _get_job_snapshot(job_id)
    if snapshot is None:
        raise ValueError(f"clone job {job_id} not found")

    payload = snapshot.get("request_json") or {}
    provider = resolve_audio_provider(
        requested_provider=payload.get("provider"),
        default_provider="elevenlabs",
    )
    adapter = get_audio_provider_adapter(provider)

    sample_file_id = str(payload.get("sample_file_id") or "").strip()
    if not sample_file_id:
        raise ValueError("clone job missing sample_file_id")

    sample_bytes = StorageService().get_bytes(sample_file_id)
    if len(sample_bytes) == 0:
        raise ValueError("clone sample is empty")

    sample_filename = sample_file_id.rsplit("/", 1)[-1] or "sample.wav"
    sample_content_type = mimetypes.guess_type(sample_filename)[0] or "audio/wav"
    clone_name = str(payload.get("name") or "").strip() or f"clone-{job_id[:8]}"
    clone_result = asyncio.run(
        adapter.clone_voice(
            name=clone_name,
            files=[sample_file_id],
            remove_background_noise=bool(payload.get("denoise", False)),
            options={
                "sample_files": [
                    {
                        "filename": sample_filename,
                        "content": sample_bytes,
                        "content_type": sample_content_type,
                    }
                ],
                "language_code": payload.get("language_code"),
                "gender": payload.get("gender"),
            },
        )
    )

    if clone_result.status != "ready" or not clone_result.provider_voice_id:
        error_text = clone_result.error_message or str(clone_result.raw or "clone_not_ready")
        raise RuntimeError(f"clone provider did not return ready voice: {error_text}")

    db = SessionLocal()
    try:
        voice = Voice(
            user_id=UUID(snapshot["user_id"]),
            name=clone_name,
            source_type="cloned",
            visibility="private",
            language_code=payload.get("language_code"),
            gender=payload.get("gender"),
            consent_status="confirmed" if payload.get("consent_confirmed") else "unknown",
            provider_status="ready",
            sample_count=1,
            external_voice_id=clone_result.provider_voice_id,
            metadata_json={
                "provider": provider,
                "clone_job_id": job_id,
                "sample_file_id": sample_file_id,
                "provider_raw": clone_result.raw,
            },
        )
        db.add(voice)
        db.commit()
        db.refresh(voice)
        return {
            "provider": provider,
            "provider_voice_id": clone_result.provider_voice_id,
            "external_voice_id": clone_result.provider_voice_id,
            "voice_profile_id": str(voice.id),
            "voice_id": str(voice.id),
            "sample_file_id": sample_file_id,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name='audio.process_clone_job', bind=True, max_retries=3)
def process_clone_job(self, job_id: str) -> dict:
    try:
        _update_job(job_id, status='processing', started_at=datetime.now(UTC))
        runtime = _execute_clone_job(job_id)
        _update_job(
            job_id,
            status='succeeded',
            runtime_json=runtime,
            finished_at=datetime.now(UTC),
        )
        return {'job_id': job_id, 'status': 'succeeded', **runtime}
    except Exception as exc:
        logger.exception("Clone task failed for %s", job_id)
        if _is_permanent_clone_error(exc) or self.request.retries >= self.max_retries:
            _update_job(
                job_id,
                status='failed',
                error_code='clone_task_error',
                error_message=str(exc),
                finished_at=datetime.now(UTC),
            )
            raise
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

        artifacts = execution.artifacts or []
        provider = artifacts[0].provider if artifacts and artifacts[0].provider else "internal_genvoice"
        runtime_json = _finalize_clone_preview_success(job_id, execution=execution, provider=provider)
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
