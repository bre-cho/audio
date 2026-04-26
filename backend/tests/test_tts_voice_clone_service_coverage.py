from __future__ import annotations

import uuid

import pytest

from app.audio_factory.schemas import AudioTaskRequest, AudioWorkflowType
from app.models.voice import Voice
from app.schemas.tts import TTSGenerateRequest, TTSPreviewRequest
from app.schemas.voice_clone import VoiceCloneCreateRequest, VoiceClonePreviewRequest
from app.services.tts_service import TTSService
from app.services.voice_clone_service import VoiceCloneService


def test_tts_submit_generate_and_preview_enqueue(db_session, monkeypatch) -> None:
    svc = TTSService(db_session)
    enqueued: list[str] = []
    credit_events: list[dict] = []

    monkeypatch.setattr("app.services.tts_service.enqueue_tts_job", lambda job_id: enqueued.append(job_id))
    monkeypatch.setattr(svc.credits, "add_event", lambda **kwargs: credit_events.append(kwargs))

    gen_payload = TTSGenerateRequest(text="hello generate")
    prev_payload = TTSPreviewRequest(text="hello preview")

    gen_out = svc.submit_generate(gen_payload)
    prev_out = svc.submit_preview(prev_payload)

    assert gen_out.job_type == "tts"
    assert prev_out.job_type == "tts_preview"
    assert enqueued == [str(gen_out.id), str(prev_out.id)]
    assert len(credit_events) == 1
    assert credit_events[0]["event_type"] == "reserve"


def test_tts_submit_generate_task_respects_idempotency(db_session, monkeypatch) -> None:
    svc = TTSService(db_session)
    enqueued: list[str] = []
    credit_events: list[dict] = []

    monkeypatch.setattr("app.services.tts_service.enqueue_tts_job", lambda job_id: enqueued.append(job_id))
    monkeypatch.setattr(svc.credits, "add_event", lambda **kwargs: credit_events.append(kwargs))

    task = AudioTaskRequest(
        workflow_type=AudioWorkflowType.TTS_GENERATE,
        request_json={"text": "hello task"},
        text="hello task",
    )
    payload = TTSGenerateRequest(text="hello task")

    idem = f"idem-tts-generate-{uuid.uuid4()}"
    first = svc.submit_generate_task(task, payload, idempotency_key=idem)
    second = svc.submit_generate_task(task, payload, idempotency_key=idem)

    assert first.id == second.id
    assert enqueued == [str(first.id)]
    assert len(credit_events) == 1


def test_tts_submit_preview_task_respects_idempotency(db_session, monkeypatch) -> None:
    svc = TTSService(db_session)
    enqueued: list[str] = []
    monkeypatch.setattr("app.services.tts_service.enqueue_tts_job", lambda job_id: enqueued.append(job_id))

    task = AudioTaskRequest(
        workflow_type=AudioWorkflowType.TTS_PREVIEW,
        request_json={"text": "hello preview task"},
        text="hello preview task",
    )
    payload = TTSPreviewRequest(text="hello preview task")

    idem = f"idem-tts-preview-task-{uuid.uuid4()}"
    first = svc.submit_preview_task(task, payload, idempotency_key=idem)
    second = svc.submit_preview_task(task, payload, idempotency_key=idem)

    assert first.id == second.id
    assert enqueued == [str(first.id)]


def test_voice_clone_submit_clone_requires_consent(db_session) -> None:
    svc = VoiceCloneService(db_session)
    payload = VoiceCloneCreateRequest(
        name="Clone A",
        provider="elevenlabs",
        language_code="en",
        sample_file_id="sample-1",
        consent_confirmed=False,
    )

    with pytest.raises(ValueError, match="consent_confirmed"):
        svc.submit_clone(payload)


def test_voice_clone_submit_clone_idempotent_enqueues_once(db_session, monkeypatch) -> None:
    svc = VoiceCloneService(db_session)
    enqueued: list[str] = []
    credit_events: list[dict] = []

    monkeypatch.setattr("app.services.voice_clone_service.enqueue_clone_job", lambda job_id: enqueued.append(job_id))
    monkeypatch.setattr(svc.credits, "add_event", lambda **kwargs: credit_events.append(kwargs))

    payload = VoiceCloneCreateRequest(
        name="Clone B",
        provider="elevenlabs",
        language_code="en",
        sample_file_id="sample-2",
        consent_confirmed=True,
    )

    idem = f"idem-clone-{uuid.uuid4()}"
    first = svc.submit_clone(payload, idempotency_key=idem)
    second = svc.submit_clone(payload, idempotency_key=idem)

    assert first.id == second.id
    assert enqueued == [str(first.id)]
    assert len(credit_events) == 1
    assert credit_events[0]["delta_credits"] == -1000


def test_voice_clone_submit_preview_and_preview_task(db_session, monkeypatch) -> None:
    svc = VoiceCloneService(db_session)
    enqueued: list[str] = []
    monkeypatch.setattr("app.services.voice_clone_service.enqueue_clone_preview_job", lambda job_id: enqueued.append(job_id))

    voice_id = uuid.uuid4()
    db_session.add(Voice(id=voice_id, name="Voice For Clone Preview"))
    db_session.commit()

    direct = svc.submit_preview(voice_id, VoiceClonePreviewRequest(text="preview direct"))

    task = AudioTaskRequest(
        workflow_type=AudioWorkflowType.CLONE_PREVIEW,
        request_json={"text": "preview task", "voice_id": str(voice_id)},
        text="preview task",
    )
    idem = f"idem-clone-preview-{uuid.uuid4()}"
    by_task_first = svc.submit_preview_task(voice_id, task, idempotency_key=idem)
    by_task_second = svc.submit_preview_task(voice_id, task, idempotency_key=idem)

    assert direct.job_type == "clone_preview"
    assert by_task_first.id == by_task_second.id
    assert enqueued == [str(direct.id), str(by_task_first.id)]