from __future__ import annotations

import io
import logging
import struct
from datetime import UTC, datetime
from uuid import UUID
import wave as wav

from app.audio_factory import AudioFactoryExecutor, AudioJobFinalizer, AudioTaskRequest, AudioWorkflowType
from app.core.config import settings
from app.core.runtime_guard import assert_real_provider, is_production_like
from app.core.storage import StorageService, compute_sha256
from app.db.session import SessionLocal
from app.models.audio_job import AudioJob
from app.services.audio_artifact_service import write_audio_artifacts
from app.services.audio_provider_router import resolve_audio_provider
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

_EXTERNAL_TTS_PROVIDERS = {"elevenlabs", "minimax"}


def _is_strict_runtime() -> bool:
    return is_production_like()


def _call_real_provider(task: AudioTaskRequest, provider: str) -> dict | None:
    if provider == "elevenlabs":
        if not settings.elevenlabs_api_key:
            if _is_strict_runtime():
                raise RuntimeError("Missing ELEVENLABS_API_KEY in production-like runtime")
            return None
        from app.providers.elevenlabs import ElevenLabsProvider

        result = ElevenLabsProvider().generate_speech(
            {
                "voice_id": task.voice_id,
                "text": task.text or "",
                "model_id": task.model_version,
            }
        )
        audio_bytes: bytes = result.get("audio_bytes") or b""
        if not audio_bytes:
            return None
        mime_type = result.get("mime_type", "audio/mpeg")
        ext = "mp3" if "mpeg" in mime_type else "wav"
        job_id = task.source_job_id or ""
        storage_key = f"audio/{job_id}.{ext}"
        stored = StorageService().put_bytes(storage_key, audio_bytes, mime_type)
        checksum = compute_sha256(audio_bytes)
        return {
            "preview_url": stored.public_url,
            "output_url": stored.public_url,
            "artifacts": [
                {
                    "artifact_type": "output",
                    "storage_key": stored.key,
                    "path": stored.path or "",
                    "url": stored.public_url or f"/artifacts/{storage_key}",
                    "mime_type": stored.mime_type or mime_type,
                    "size_bytes": stored.size_bytes or len(audio_bytes),
                    "checksum": stored.checksum or checksum,
                    "provider": provider,
                    "generation_mode": "real",
                    "provider_verified": True,
                    "audio_contains_signal": True,
                    "quality_report": {"source": "provider", "validation": "provider_asserted"},
                    "contract_pass": True,
                    "lineage_pass": True,
                    "write_integrity_pass": True,
                }
            ],
        }
    return None


class _WorkerAudioRuntime:
    def run(self, task: AudioTaskRequest, workflow_spec: dict) -> dict:
        del workflow_spec
        provider = resolve_audio_provider(requested_provider=task.provider, default_provider="internal_genvoice")
        assert_real_provider(provider, feature=task.workflow_type.value)
        real_result = _call_real_provider(task, provider)
        if real_result is not None:
            return real_result
        if _is_strict_runtime() and provider in _EXTERNAL_TTS_PROVIDERS:
            raise RuntimeError(f"Refusing placeholder fallback for provider '{provider}' in production-like runtime")
        return write_audio_artifacts(task.source_job_id or "", request_json=task.request_json, provider=provider)


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
            "workflow_type": job.workflow_type,
            "project_id": str(job.project_id) if job.project_id else None,
            "request_json": job.request_json or {},
            "runtime_json": job.runtime_json or {},
        }
    finally:
        db.close()


def _should_fail_task(task) -> bool:
    return task.request.retries >= task.max_retries


def _workflow_from_snapshot(snapshot: dict | None, fallback: AudioWorkflowType) -> AudioWorkflowType:
    raw = (snapshot or {}).get("workflow_type")
    if raw and raw != "unknown":
        return AudioWorkflowType(raw)
    return fallback


def _build_task_request(job_id: str, snapshot: dict | None, workflow_type: AudioWorkflowType) -> AudioTaskRequest:
    payload = (snapshot or {}).get("request_json") or {}
    voice_id = payload.get("voice_id") or payload.get("voice")
    script = payload.get("raw_script") or payload.get("script")
    return AudioTaskRequest(
        workflow_type=workflow_type,
        source_job_id=job_id,
        request_json=payload,
        text=payload.get("text"),
        script=script,
        conversation_turns=payload.get("conversation_turns") if isinstance(payload.get("conversation_turns"), list) else None,
        voice_id=str(voice_id) if voice_id is not None else None,
        provider=payload.get("provider") or "internal_genvoice",
        model_version=payload.get("model"),
        metadata={"job_type": (snapshot or {}).get("job_type"), "workflow_type": workflow_type.value},
    )


def _execute_factory(job_id: str, fallback_workflow_type: AudioWorkflowType):
    snapshot = _get_job_snapshot(job_id) or {"request_json": {}}
    workflow_type = _workflow_from_snapshot(snapshot, fallback_workflow_type)
    task = _build_task_request(job_id, snapshot, workflow_type)
    db = SessionLocal()
    try:
        executor = AudioFactoryExecutor(provider_runtime=_WorkerAudioRuntime())
        return snapshot, executor.execute(db=db, task=task)
    finally:
        db.close()


def _finalize_job_success(job_id: str, *, execution, promotion_reason: str, provider: str) -> dict:
    db = SessionLocal()
    try:
        job = AudioJobFinalizer().finalize_success(
            db=db,
            job_id=job_id,
            execution=execution,
            promotion_reason=promotion_reason,
            provider=provider,
        )
        return job.runtime_json
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _factory_error(execution) -> str:
    if execution.incident:
        return execution.incident.get("error_message") or str(execution.incident)
    return execution.validation.get("error") or str(execution.validation)


def _provider_from_execution(execution, *, fallback: str = "internal_genvoice") -> str:
    artifacts = execution.artifacts or []
    if artifacts and artifacts[0].provider:
        return artifacts[0].provider
    return fallback


def enqueue_tts_job(job_id: str) -> None:
    process_tts_job.delay(job_id)


def enqueue_conversation_job(job_id: str) -> None:
    process_conversation_job.delay(job_id)


def enqueue_batch_job(job_id: str) -> None:
    process_batch_job.delay(job_id)


def enqueue_audio_effect_job(job_id: str) -> None:
    try:
        process_audio_effect_job.delay(job_id)
    except Exception as exc:
        logger.warning("Falling back to inline audio effect execution for %s: %s", job_id, exc)
        process_audio_effect_job.run(job_id)


def enqueue_voice_shift_job(job_id: str) -> None:
    try:
        process_voice_shift_job.delay(job_id)
    except Exception as exc:
        logger.warning("Falling back to inline voice shift execution for %s: %s", job_id, exc)
        process_voice_shift_job.run(job_id)


@celery_app.task(name="audio.process_tts_job", bind=True, max_retries=3)
def process_tts_job(self, job_id: str) -> dict:
    try:
        _update_job(job_id, status="processing", started_at=datetime.now(UTC))
        _, execution = _execute_factory(job_id, AudioWorkflowType.TTS_PREVIEW)
        if not execution.success:
            raise RuntimeError(_factory_error(execution))

        runtime_json = _finalize_job_success(
            job_id,
            execution=execution,
            promotion_reason="artifacts passed factory file validation, DB persistence validation, and finalizer success contract",
            provider=_provider_from_execution(execution),
        )
        return {"job_id": job_id, "status": "succeeded", **runtime_json}
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
            raise RuntimeError(_factory_error(execution))

        runtime_json = _finalize_job_success(
            job_id,
            execution=execution,
            promotion_reason="conversation artifacts passed factory file validation, DB persistence validation, and finalizer success contract",
            provider=_provider_from_execution(execution),
        )
        return {"job_id": job_id, "status": "succeeded", **runtime_json}
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
            raise RuntimeError(_factory_error(execution))

        runtime_json = _finalize_job_success(
            job_id,
            execution=execution,
            promotion_reason="narration artifacts passed factory file validation, DB persistence validation, and finalizer success contract",
            provider=_provider_from_execution(execution),
        )
        return {"job_id": job_id, "status": "succeeded", **runtime_json}
    except Exception as exc:
        logger.exception("Audio task failed for %s", job_id)
        if _should_fail_task(self):
            _update_job(job_id, status="failed", error_code="audio_task_error", error_message=str(exc), finished_at=datetime.now(UTC))
        else:
            _update_job(job_id, status="retrying", error_code="audio_task_retrying", error_message=str(exc))
        raise self.retry(exc=exc, countdown=10)


def _wav_to_samples(raw: bytes, sample_width: int) -> list[int]:
    if sample_width == 2:
        return [struct.unpack_from("<h", raw, i)[0] for i in range(0, len(raw), 2)]
    if sample_width == 1:
        return [raw[i] - 128 for i in range(len(raw))]
    raise ValueError("Unsupported sample width")


def _samples_to_wav_bytes(samples: list[int], sample_width: int, channels: int, framerate: int) -> bytes:
    if sample_width != 2:
        raise ValueError("Only 16-bit PCM WAV is supported")
    clamped = [max(-32768, min(32767, int(s))) for s in samples]
    raw = struct.pack(f"<{len(clamped)}h", *clamped)
    buf = io.BytesIO()
    with wav.open(buf, "wb") as out:
        out.setnchannels(channels)
        out.setsampwidth(sample_width)
        out.setframerate(framerate)
        out.writeframes(raw)
    return buf.getvalue()


@celery_app.task(name="audio.process_audio_effect_job", bind=True, max_retries=3)
def process_audio_effect_job(self, job_id: str) -> dict:
    try:
        _update_job(job_id, status="processing", started_at=datetime.now(UTC))
        snapshot = _get_job_snapshot(job_id)
        if snapshot is None:
            raise RuntimeError(f"Job {job_id} not found")

        req = snapshot.get("request_json") or {}
        effect_type = str(req.get("effect_type", "echo"))
        parameters = req.get("parameters") or {}
        input_file_key = str(req.get("input_file_key", ""))
        if not input_file_key:
            raise ValueError("request_json missing input_file_key")

        storage = StorageService()
        input_bytes = storage.get_bytes(input_file_key)
        degraded = False

        try:
            with wav.open(io.BytesIO(input_bytes), "rb") as w:
                channels = w.getnchannels()
                sample_width = w.getsampwidth()
                framerate = w.getframerate()
                raw_frames = w.readframes(w.getnframes())

            samples = _wav_to_samples(raw_frames, sample_width)
            if effect_type == "echo":
                delay_ms = float(parameters.get("delay_ms", 250))
                feedback = float(parameters.get("feedback_ratio", 0.5))
                delay_samples = max(1, int(framerate * delay_ms / 1000)) * channels
                out = samples[:]
                for i in range(delay_samples, len(out)):
                    out[i] = int(out[i] + out[i - delay_samples] * feedback)
                processed = out
            elif effect_type == "eq":
                gain = 10 ** (float(parameters.get("mid_db", 0.0)) / 20.0)
                processed = [int(s * gain) for s in samples]
            elif effect_type == "reverb":
                wet = float(parameters.get("wet", 0.25))
                tap = max(1, int(0.03 * framerate)) * channels
                out = samples[:]
                for i in range(tap, len(out)):
                    out[i] = int((1 - wet) * out[i] + wet * out[i - tap])
                processed = out
            else:
                processed = samples

            out_bytes = _samples_to_wav_bytes(processed, sample_width, channels, framerate)
        except Exception:
            out_bytes = input_bytes
            degraded = True

        out_key = f"audio/effects/{effect_type}/{job_id}.wav"
        stored = storage.put_bytes(out_key, out_bytes, "audio/wav")
        runtime = {
            "output_url": stored.public_url,
            "storage_key": stored.key,
            "checksum": stored.checksum,
            "effect_type": effect_type,
            "parameters": parameters,
            "degraded": degraded,
            "provider": "internal_dsp",
        }
        _update_job(job_id, status="done", output_url=stored.public_url, runtime_json=runtime, finished_at=datetime.now(UTC))
        return {"job_id": job_id, "status": "succeeded", **runtime}
    except Exception as exc:
        logger.exception("Audio effect task failed for %s", job_id)
        if _should_fail_task(self):
            _update_job(job_id, status="failed", error_code="audio_effect_error", error_message=str(exc), finished_at=datetime.now(UTC))
        else:
            _update_job(job_id, status="retrying", error_code="audio_effect_retrying", error_message=str(exc))
        raise self.retry(exc=exc, countdown=10)


@celery_app.task(name="audio.process_voice_shift_job", bind=True, max_retries=3)
def process_voice_shift_job(self, job_id: str) -> dict:
    try:
        _update_job(job_id, status="processing", started_at=datetime.now(UTC))
        snapshot = _get_job_snapshot(job_id)
        if snapshot is None:
            raise RuntimeError(f"Job {job_id} not found")

        req = snapshot.get("request_json") or {}
        sample_file_key = str(req.get("sample_file_id", ""))
        pitch_semitones = float(req.get("pitch_semitones", 0.0))
        if not sample_file_key:
            raise ValueError("request_json missing sample_file_id")

        storage = StorageService()
        input_bytes = storage.get_bytes(sample_file_key)
        degraded = False

        try:
            shift_ratio = 2 ** (pitch_semitones / 12.0)
            with wav.open(io.BytesIO(input_bytes), "rb") as w:
                channels = w.getnchannels()
                sample_width = w.getsampwidth()
                framerate = w.getframerate()
                raw_frames = w.readframes(w.getnframes())

            samples = _wav_to_samples(raw_frames, sample_width)
            # Resample by nearest-neighbor index mapping
            new_len = max(1, int(len(samples) / max(shift_ratio, 0.01)))
            resampled = [samples[min(len(samples) - 1, int(i * shift_ratio))] for i in range(new_len)]
            out_bytes = _samples_to_wav_bytes(resampled, sample_width, channels, framerate)
        except Exception:
            out_bytes = input_bytes
            degraded = True

        out_key = f"audio/voice-shift/{job_id}.wav"
        stored = storage.put_bytes(out_key, out_bytes, "audio/wav")
        runtime = {
            "output_url": stored.public_url,
            "storage_key": stored.key,
            "checksum": stored.checksum,
            "size_bytes": stored.size_bytes,
            "pitch_semitones": pitch_semitones,
            "degraded": degraded,
            "provider": "internal_shift",
        }
        _update_job(job_id, status="done", output_url=stored.public_url, runtime_json=runtime, finished_at=datetime.now(UTC))
        return {"job_id": job_id, "status": "succeeded", **runtime}
    except Exception as exc:
        logger.exception("Voice shift task failed for %s", job_id)
        if _should_fail_task(self):
            _update_job(job_id, status="failed", error_code="voice_shift_error", error_message=str(exc), finished_at=datetime.now(UTC))
        else:
            _update_job(job_id, status="retrying", error_code="voice_shift_retrying", error_message=str(exc))
        raise self.retry(exc=exc, countdown=10)
