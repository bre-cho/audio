from __future__ import annotations

import uuid

import pytest

from app.core.storage import StorageService
from app.models.audio_job import AudioJob
from app.models.voice import Voice
from app.services.audio.provider_base import AudioCloneResult
from app.workers.clone_tasks import process_clone_job


class _ReadyCloneAdapter:
    async def clone_voice(self, **kwargs) -> AudioCloneResult:
        del kwargs
        return AudioCloneResult(
            provider="elevenlabs",
            provider_voice_id="el_voice_123",
            status="ready",
            raw={"voice_id": "el_voice_123"},
        )


def test_process_clone_job_creates_voice_and_runtime(db_session, monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path))
    stored = StorageService().put_bytes("voice-clone/samples/test.wav", b"RIFFdemo-audio", "audio/wav")

    job = AudioJob(
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        job_type="clone",
        workflow_type="clone",
        status="queued",
        request_json={
            "name": "Clone Real",
            "provider": "elevenlabs",
            "language_code": "en",
            "gender": "female",
            "sample_file_id": stored.key,
            "denoise": True,
            "consent_confirmed": True,
        },
        runtime_json={},
    )
    db_session.add(job)
    db_session.commit()

    monkeypatch.setattr("app.workers.clone_tasks.get_audio_provider_adapter", lambda provider: _ReadyCloneAdapter())

    result = process_clone_job.run(str(job.id))

    db_session.refresh(job)
    assert result["status"] == "succeeded"
    assert job.status == "succeeded"
    assert job.runtime_json["provider"] == "elevenlabs"
    assert job.runtime_json["provider_voice_id"] == "el_voice_123"

    voice_id = uuid.UUID(job.runtime_json["voice_id"])
    voice = db_session.query(Voice).filter(Voice.id == voice_id).one_or_none()
    assert voice is not None
    assert voice.external_voice_id == "el_voice_123"
    assert voice.provider_status == "ready"
    assert voice.source_type == "cloned"


def test_process_clone_job_missing_sample_fails_permanently(db_session) -> None:
    job = AudioJob(
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        job_type="clone",
        workflow_type="clone",
        status="queued",
        request_json={
            "name": "Clone Missing Sample",
            "provider": "elevenlabs",
            "language_code": "en",
            "consent_confirmed": True,
        },
        runtime_json={},
    )
    db_session.add(job)
    db_session.commit()

    with pytest.raises(ValueError, match="sample_file_id"):
        process_clone_job.run(str(job.id))

    db_session.refresh(job)
    assert job.status == "failed"
    assert job.error_code == "clone_task_error"
