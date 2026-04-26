from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.api.observability import _collect_audio_metrics
from app.models.audio_job import AudioJob
from app.models.project import Project
from app.models.script_asset import ScriptAsset
from app.schemas.project import ProjectCreate, ProjectScriptCreate, ProjectUpdate
from app.services.project_service import ProjectService
from app.services import provider_router


def test_provider_router_resolve_requested_and_default(monkeypatch) -> None:
    class _Eleven:
        pass

    class _Minimax:
        pass

    class _Internal:
        pass

    monkeypatch.setattr(provider_router, "ElevenLabsProvider", _Eleven)
    monkeypatch.setattr(provider_router, "MinimaxProvider", _Minimax)
    monkeypatch.setattr(provider_router, "InternalGenVoiceProvider", _Internal)
    monkeypatch.setattr(provider_router.settings, "default_provider", "minimax")

    router = provider_router.ProviderRouter()
    assert isinstance(router.resolve("elevenlabs"), _Eleven)
    assert isinstance(router.resolve("minimax"), _Minimax)
    assert isinstance(router.resolve("internal_genvoice"), _Internal)
    assert isinstance(router.resolve(None), _Minimax)

    with pytest.raises(ValueError, match="khong duoc ho tro"):
        router.resolve("unknown")


def test_project_service_crud_and_add_script(db_session) -> None:
    svc = ProjectService(db_session)

    created = svc.create_project(ProjectCreate(title="Coverage Project", description="d"))
    listed = svc.list_projects()
    fetched = svc.get_project(created.id)
    updated = svc.update_project(created.id, ProjectUpdate(title="Updated", status="active"))

    assert any(item.id == created.id for item in listed)
    assert fetched is not None
    assert fetched.title == "Coverage Project"
    assert updated is not None
    assert updated.title == "Updated"
    assert updated.status == "active"

    script = svc.add_script(
        created.id,
        ProjectScriptCreate(asset_type="dialogue", title="s1", raw_text="A: hi", language_code="en"),
    )
    assert "script_asset_id" in script

    script_row = db_session.query(ScriptAsset).filter(ScriptAsset.id == uuid.UUID(script["script_asset_id"])).one()
    assert script_row.project_id == created.id
    assert script_row.raw_text == "A: hi"


def test_project_service_get_update_missing_returns_none(db_session) -> None:
    svc = ProjectService(db_session)
    missing_id = uuid.uuid4()
    assert svc.get_project(missing_id) is None
    assert svc.update_project(missing_id, ProjectUpdate(title="x")) is None


def test_project_service_submit_batch_generate_creates_narration_and_enqueues(db_session, monkeypatch) -> None:
    svc = ProjectService(db_session)
    project = Project(user_id=svc.default_user_id, title="P", description=None)
    db_session.add(project)
    db_session.commit()

    enqueued: list[str] = []
    monkeypatch.setattr("app.services.project_service.enqueue_batch_job", lambda job_id: enqueued.append(job_id))

    out = svc.submit_batch_generate(project.id)

    job = db_session.query(AudioJob).filter(AudioJob.id == out.id).one()
    assert job.job_type == "narration"
    assert job.workflow_type == "narration"
    assert job.request_json["project_id"] == str(project.id)
    assert enqueued == [str(job.id)]


def test_collect_audio_metrics_counts_and_success_timestamps(db_session) -> None:
    now = datetime.now(UTC)
    before = _collect_audio_metrics(db_session)
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    jobs = [
        AudioJob(user_id=user_id, job_type="tts_preview", workflow_type="tts_preview", status="queued", request_json={}),
        AudioJob(user_id=user_id, job_type="narration", workflow_type="narration", status="processing", request_json={}),
        AudioJob(user_id=user_id, job_type="clone", workflow_type="clone", status="failed", request_json={}),
        AudioJob(user_id=user_id, job_type="tts_preview", workflow_type="tts_preview", status="succeeded", request_json={}, updated_at=now - timedelta(minutes=4)),
        AudioJob(user_id=user_id, job_type="narration", workflow_type="narration", status="success", request_json={}, updated_at=now - timedelta(minutes=3)),
        AudioJob(user_id=user_id, job_type="clone", workflow_type="clone", status="done", request_json={}, updated_at=now - timedelta(minutes=2)),
    ]
    db_session.add_all(jobs)
    db_session.commit()

    metrics = _collect_audio_metrics(db_session)

    assert metrics["audio_voice_clone_queue_depth"] - before["audio_voice_clone_queue_depth"] == 2.0
    assert metrics["audio_narration_queue_depth"] - before["audio_narration_queue_depth"] == 2.0
    assert metrics["audio_audio_mix_queue_depth"] - before["audio_audio_mix_queue_depth"] == 1.0
    assert metrics["audio_jobs_stuck_total"] - before["audio_jobs_stuck_total"] == 1.0
    assert metrics["audio_preview_last_success_timestamp_seconds"] > 0
    assert metrics["audio_narration_last_success_timestamp_seconds"] > 0
    assert metrics["audio_clone_last_success_timestamp_seconds"] > 0
    assert metrics["audio_clone_preview_last_success_timestamp_seconds"] >= 0.0


def test_prometheus_endpoint_returns_metrics_payload(client, db_session) -> None:
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    db_session.add(
        AudioJob(user_id=user_id, job_type="tts_preview", workflow_type="tts_preview", status="queued", request_json={})
    )
    db_session.commit()

    response = client.get("/api/v1/observability/prometheus")

    assert response.status_code == 200
    text = response.text
    assert "# HELP audio_voice_clone_queue_depth" in text
    assert "# TYPE audio_narration_queue_depth gauge" in text
    assert "audio_narration_queue_depth" in text
    assert "audio_preview_last_success_timestamp_seconds" in text