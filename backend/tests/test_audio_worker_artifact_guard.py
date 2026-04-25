from pathlib import Path

from app.models.audio_output import AudioOutput
from app.repositories.job_repo import JobRepository
from app.workers.audio_tasks import process_tts_job
from app.workers.clone_tasks import process_clone_preview_job


def _assert_contract_metadata(artifact: dict, *, expected_job_id: str, expected_type: str) -> None:
    assert artifact["source_job_id"] == expected_job_id
    assert artifact["job_id"] == expected_job_id
    assert artifact["artifact_type"] == expected_type
    assert artifact["contract_pass"] is True
    assert artifact["lineage_pass"] is True
    assert artifact["write_integrity_pass"] is True
    assert artifact["promotion_status"] == "contract_verified"
    assert artifact["replayability_status"] == "pending"
    assert artifact["determinism_status"] == "pending"
    assert artifact["drift_budget_status"] == "pending"
    assert artifact["replayability_pass"] is False
    assert artifact["determinism_pass"] is False
    assert artifact["drift_budget_pass"] is False
    assert isinstance(artifact["size_bytes"], int)
    assert artifact["size_bytes"] > 0
    assert isinstance(artifact["checksum"], str)
    assert len(artifact["checksum"]) == 64


def test_audio_worker_creates_and_persists_contract_artifacts(db_session, tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path))

    repo = JobRepository(db_session)
    job = repo.create(
        user_id="00000000-0000-0000-0000-000000000001",
        job_type="tts_preview",
        request_json={"text": "hello world", "voice": "default"},
    )

    result = process_tts_job.run(str(job.id))

    db_session.expire_all()
    updated = repo.get(job.id)
    outputs = (
        db_session.query(AudioOutput)
        .filter(AudioOutput.job_id == job.id)
        .order_by(AudioOutput.output_type.asc())
        .all()
    )

    assert result["status"] == "succeeded"
    assert updated.status == "succeeded"
    assert updated.preview_url == f"/artifacts/audio/{job.id}.preview.wav"
    assert updated.output_url == f"/artifacts/audio/{job.id}.wav"
    assert updated.runtime_json["artifact_contract_version"] == result["artifact_contract_version"]
    assert len(updated.runtime_json["artifacts"]) == 2

    preview_path = tmp_path / "audio" / f"{job.id}.preview.wav"
    output_path = tmp_path / "audio" / f"{job.id}.wav"
    assert preview_path.exists()
    assert output_path.exists()

    assert len(outputs) == 2
    output_by_type = {row.output_type: row for row in outputs}
    assert set(output_by_type) == {"output", "preview"}

    for artifact in updated.runtime_json["artifacts"]:
        _assert_contract_metadata(artifact, expected_job_id=str(job.id), expected_type=artifact["artifact_type"])
        row = output_by_type[artifact["artifact_type"]]
        assert row.public_url == artifact["url"]
        assert row.storage_key == artifact["storage_key"]
        assert row.size_bytes == artifact["size_bytes"]
        assert row.checksum == artifact["checksum"]
        assert row.waveform_json["artifact_id"] == artifact["artifact_id"]
        assert Path(artifact["path"]).exists()


def test_clone_preview_worker_creates_and_persists_contract_artifact(db_session, tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path))

    repo = JobRepository(db_session)
    job = repo.create(
        user_id="00000000-0000-0000-0000-000000000001",
        job_type="clone_preview",
        request_json={"voice": "default"},
    )

    result = process_clone_preview_job.run(str(job.id))

    db_session.expire_all()
    updated = repo.get(job.id)
    outputs = db_session.query(AudioOutput).filter(AudioOutput.job_id == job.id).all()

    assert result["status"] == "succeeded"
    assert updated.status == "succeeded"
    assert result["preview_url"] == f"/artifacts/audio/{job.id}.clone_preview.wav"
    assert len(result["artifacts"]) == 1
    assert len(updated.runtime_json["artifacts"]) == 1
    assert updated.runtime_json["promotion_gate"]["promotion_status"] == "contract_verified"

    artifact = updated.runtime_json["artifacts"][0]
    _assert_contract_metadata(artifact, expected_job_id=str(job.id), expected_type="clone_preview")

    assert Path(tmp_path / "audio" / f"{job.id}.clone_preview.wav").exists()
    assert len(outputs) == 1
    assert outputs[0].output_type == "clone_preview"
    assert outputs[0].public_url == artifact["url"]
    assert outputs[0].storage_key == artifact["storage_key"]
    assert outputs[0].size_bytes == artifact["size_bytes"]
    assert outputs[0].checksum == artifact["checksum"]
    assert outputs[0].waveform_json["artifact_id"] == artifact["artifact_id"]
