from __future__ import annotations

import pytest

from app.audio_factory.job_finalizer import AudioJobFinalizer, AudioJobFinalizerError
from app.audio_factory.schemas import AudioArtifactContract, AudioFactoryResult, AudioWorkflowType
from app.repositories.job_repo import JobRepository


def test_finalizer_rejects_empty_artifacts(db_session):
    repo = JobRepository(db_session)
    job = repo.create(
        user_id="00000000-0000-0000-0000-000000000001",
        job_type="tts_preview",
        request_json={"text": "hello"},
    )

    execution = AudioFactoryResult(
        success=True,
        workflow_type=AudioWorkflowType.TTS_PREVIEW,
        job_id=str(job.id),
        artifacts=[],
        validation={
            "file": {"passed": True},
            "db": {"passed": True},
        },
    )

    with pytest.raises(AudioJobFinalizerError, match="artifacts"):
        AudioJobFinalizer().finalize_success(
            db=db_session,
            job_id=str(job.id),
            execution=execution,
            promotion_reason="unit test",
        )

    db_session.refresh(job)
    assert job.status != "succeeded"


def test_finalizer_rejects_missing_db_output_even_if_factory_claims_success(db_session):
    repo = JobRepository(db_session)
    job = repo.create(
        user_id="00000000-0000-0000-0000-000000000001",
        job_type="tts_preview",
        request_json={"text": "hello"},
    )

    artifact = AudioArtifactContract(
        artifact_id="artifact-unit-test",
        artifact_type="preview",
        source_job_id=str(job.id),
        job_id=str(job.id),
        storage_key="unit/preview.wav",
        path="/tmp/unit/preview.wav",
        url="/artifacts/unit/preview.wav",
        public_url="/artifacts/unit/preview.wav",
        mime_type="audio/wav",
        size_bytes=100,
        checksum="a" * 64,
        promotion_status="contract_verified",
    )
    execution = AudioFactoryResult(
        success=True,
        workflow_type=AudioWorkflowType.TTS_PREVIEW,
        job_id=str(job.id),
        artifacts=[artifact],
        preview_url="/artifacts/unit/preview.wav",
        output_url=None,
        artifact_contract_version="unit",
        validation={
            "file": {"passed": True},
            "db": {"passed": True},
        },
    )

    with pytest.raises(AudioJobFinalizerError, match="Missing audio_outputs row"):
        AudioJobFinalizer().finalize_success(
            db=db_session,
            job_id=str(job.id),
            execution=execution,
            promotion_reason="unit test",
        )

    db_session.refresh(job)
    assert job.status != "succeeded"
