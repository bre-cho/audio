from pathlib import Path

from app.repositories.job_repo import JobRepository
from app.workers.audio_tasks import process_tts_job


def test_audio_worker_creates_artifacts(db_session, tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path))
    monkeypatch.setenv("AUDIO_ARTIFACT_DIR", str(tmp_path / "audio"))

    import app.services.audio_artifact_service as svc
    svc.AUDIO_ARTIFACT_DIR = str(tmp_path / "audio")

    repo = JobRepository(db_session)
    job = repo.create(
        user_id="00000000-0000-0000-0000-000000000001",
        job_type="tts_preview",
        request_json={"text": "hello world", "voice": "default"},
    )

    result = process_tts_job.run(str(job.id))

    db_session.expire_all()
    updated = repo.get(job.id)

    assert result["status"] == "succeeded"
    assert updated.status == "succeeded"
    assert updated.preview_url == f"/artifacts/audio/{job.id}.preview.mp3"
    assert updated.output_url == f"/artifacts/audio/{job.id}.mp3"

    assert Path(tmp_path / "audio" / f"{job.id}.preview.mp3").exists()
    assert Path(tmp_path / "audio" / f"{job.id}.mp3").exists()
