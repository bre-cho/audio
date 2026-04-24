from __future__ import annotations

from unittest.mock import patch

import pytest
from celery.exceptions import Retry

from app.repositories.job_repo import JobRepository

VALID_STATUSES = {"queued", "processing", "retrying", "succeeded", "failed"}


def test_retrying_state_not_failed_before_max_retries():
    assert "retrying" in VALID_STATUSES


def test_retrying_status_set_before_max_retries(db_session, tmp_path, monkeypatch):
    """On a non-final retry attempt the job status must be set to 'retrying', not 'failed'."""
    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path))
    monkeypatch.setenv("AUDIO_ARTIFACT_DIR", str(tmp_path / "audio"))

    import app.services.audio_artifact_service as svc
    svc.AUDIO_ARTIFACT_DIR = str(tmp_path / "audio")

    repo = JobRepository(db_session)
    job = repo.create(
        user_id="00000000-0000-0000-0000-000000000001",
        job_type="tts_preview",
        request_json={"text": "hello", "voice": "default"},
    )

    from app.workers.audio_tasks import process_tts_job

    # _should_fail_task returns False → non-final retry → expect 'retrying' status
    with patch("app.workers.audio_tasks._should_fail_task", return_value=False), \
         patch(
             "app.workers.audio_tasks.write_audio_artifacts",
             side_effect=RuntimeError("transient error"),
         ), \
         patch("app.workers.audio_tasks.process_tts_job.retry", side_effect=Retry):
        with pytest.raises(Retry):
            process_tts_job.run(str(job.id))

    db_session.expire_all()
    updated = repo.get(job.id)
    assert updated.status == "retrying", f"expected 'retrying', got '{updated.status}'"
    assert updated.error_code == "audio_task_retrying"


def test_failed_status_set_on_final_retry(db_session, tmp_path, monkeypatch):
    """On the final retry attempt the job status must be set to 'failed'."""
    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path))
    monkeypatch.setenv("AUDIO_ARTIFACT_DIR", str(tmp_path / "audio"))

    import app.services.audio_artifact_service as svc
    svc.AUDIO_ARTIFACT_DIR = str(tmp_path / "audio")

    repo = JobRepository(db_session)
    job = repo.create(
        user_id="00000000-0000-0000-0000-000000000001",
        job_type="tts_preview",
        request_json={"text": "hello", "voice": "default"},
    )

    from app.workers.audio_tasks import process_tts_job

    # _should_fail_task returns True → final retry → expect 'failed' status
    with patch("app.workers.audio_tasks._should_fail_task", return_value=True), \
         patch(
             "app.workers.audio_tasks.write_audio_artifacts",
             side_effect=RuntimeError("permanent error"),
         ), \
         patch("app.workers.audio_tasks.process_tts_job.retry", side_effect=Retry):
        with pytest.raises(Retry):
            process_tts_job.run(str(job.id))

    db_session.expire_all()
    updated = repo.get(job.id)
    assert updated.status == "failed", f"expected 'failed', got '{updated.status}'"
    assert updated.error_code == "audio_task_error"
    assert updated.finished_at is not None
