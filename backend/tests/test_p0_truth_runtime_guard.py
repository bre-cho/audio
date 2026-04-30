from __future__ import annotations

import pytest

from app.audio_factory.job_finalizer import AudioJobFinalizer, AudioJobFinalizerError
from app.audio_factory.schemas import AudioArtifactContract
from app.core.config import settings
from app.core.runtime_guard import RuntimeGuardError
from app.services.audio_artifact_service import write_audio_artifacts
from app.services.audio_provider_router import resolve_audio_provider
from app.services.audio_quality.audio_signal_validator import validate_wav_signal


def test_audio_signal_validator_blocks_silent_wav() -> None:
    silent = b"RIFF\x24\x7d\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00}\x00\x00" + b"\x00\x00" * 16000
    report = validate_wav_signal(silent)
    assert report.passed is False
    assert report.reason in {"silent_or_near_silent", "duration_too_short"}


def test_write_audio_artifacts_marks_placeholder_blocked_in_strict_runtime(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path))
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "provider_strict_mode", True)
    monkeypatch.setattr(settings, "allow_placeholder_audio", True)

    result = write_audio_artifacts("00000000-0000-0000-0000-000000000123", request_json={"text": "hello"}, provider="internal_genvoice")

    assert len(result["artifacts"]) == 2
    for artifact in result["artifacts"]:
        assert artifact["generation_mode"] == "placeholder"
        assert artifact["audio_contains_signal"] is False
        assert artifact["provider_verified"] is False
        assert artifact["promotion_status"] == "blocked"


def test_audio_provider_router_blocks_placeholder_provider_in_strict_runtime(monkeypatch) -> None:
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "provider_strict_mode", True)

    with pytest.raises(RuntimeGuardError, match="Blocked placeholder provider"):
        resolve_audio_provider(requested_provider="internal_genvoice")


def test_finalizer_rejects_placeholder_artifacts_in_strict_runtime(monkeypatch) -> None:
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "provider_strict_mode", True)

    artifact = AudioArtifactContract(
        artifact_id="artifact-strict-p0",
        artifact_type="preview",
        source_job_id="job-1",
        job_id="job-1",
        storage_key="unit/preview.wav",
        path="/tmp/unit/preview.wav",
        url="/artifacts/unit/preview.wav",
        public_url="/artifacts/unit/preview.wav",
        mime_type="audio/wav",
        size_bytes=100,
        checksum="a" * 64,
        promotion_status="contract_verified",
        generation_mode="placeholder",
        provider_verified=False,
        audio_contains_signal=False,
    )

    with pytest.raises(AudioJobFinalizerError, match="generation_mode must be real"):
        AudioJobFinalizer()._assert_artifact_truth_gates([artifact])
