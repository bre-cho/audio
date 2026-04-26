from __future__ import annotations

import asyncio
import uuid

import pytest

from app.models.voice import Voice
from app.repositories.project_repo import ProjectRepository
from app.repositories.voice_repo import VoiceRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.voice import VoiceListFilters, VoiceUpdate
from app.services.audio.providers.elevenlabs_provider import ElevenLabsAudioProvider
from app.services import audio_provider_router as provider_router


def test_elevenlabs_list_voices_maps_and_skips_invalid(monkeypatch) -> None:
    class _FakeElevenLabsProvider:
        def list_voices(self):
            return [
                {"voice_id": "v1", "name": "Voice One", "labels": {"language": "en", "gender": "female"}, "preview_url": "u1"},
                {"shared_voice_id": "v2", "name": "Voice Two", "labels": {"language": "vi"}},
                {"name": "Missing Id"},
            ]

    monkeypatch.setattr(
        "app.services.audio.providers.elevenlabs_provider.ElevenLabsProvider",
        _FakeElevenLabsProvider,
    )

    adapter = ElevenLabsAudioProvider()
    voices = asyncio.run(adapter.list_voices())

    assert len(voices) == 2
    assert voices[0].voice_id == "v1"
    assert voices[0].display_name == "Voice One"
    assert voices[0].language_code == "en"
    assert voices[0].gender == "female"
    assert voices[1].voice_id == "v2"
    assert voices[1].display_name == "Voice Two"


def test_elevenlabs_synthesize_and_compose_music_payloads(monkeypatch) -> None:
    calls: list[dict] = []

    class _FakeElevenLabsProvider:
        def generate_speech(self, payload: dict) -> dict:
            calls.append(payload)
            return {"audio_bytes": b"audio-data"}

    monkeypatch.setattr(
        "app.services.audio.providers.elevenlabs_provider.ElevenLabsProvider",
        _FakeElevenLabsProvider,
    )

    adapter = ElevenLabsAudioProvider()

    synth = asyncio.run(adapter.synthesize_speech(voice_id="v1", text="hello"))
    assert synth.provider == "elevenlabs"
    assert synth.audio_bytes == b"audio-data"
    assert synth.output_format == "mp3_44100_128"

    music = asyncio.run(adapter.compose_music(prompt_text="calm", duration_seconds=15, force_instrumental=False))
    assert music.provider == "elevenlabs"
    assert music.audio_bytes == b"audio-data"
    assert music.output_format == "mp3"

    assert calls[0]["voice_id"] == "v1"
    assert calls[0]["text"] == "hello"
    assert calls[1]["prompt_text"] == "calm"
    assert calls[1]["duration_seconds"] == 15
    assert calls[1]["force_instrumental"] is False


def test_elevenlabs_clone_voice_success_and_failure(monkeypatch) -> None:
    class _FakeElevenLabsProvider:
        def __init__(self) -> None:
            self._responses = iter(
                [
                    {"status": "ok", "voice_id": "new-voice"},
                    {"status": "error", "error": "boom"},
                ]
            )

        def clone_voice(self, payload: dict) -> dict:
            assert payload["name"] == "sample"
            assert payload["files"] == ["a.wav"]
            assert payload["remove_background_noise"] is True
            return next(self._responses)

    monkeypatch.setattr(
        "app.services.audio.providers.elevenlabs_provider.ElevenLabsProvider",
        _FakeElevenLabsProvider,
    )

    adapter = ElevenLabsAudioProvider()
    success = asyncio.run(adapter.clone_voice(name="sample", files=["a.wav"]))
    failure = asyncio.run(adapter.clone_voice(name="sample", files=["a.wav"]))

    assert success.status == "ready"
    assert success.provider_voice_id == "new-voice"
    assert failure.status == "failed"
    assert failure.provider_voice_id is None
    assert failure.error_message == "boom"


def test_audio_provider_router_normalize_resolve_and_cache(monkeypatch) -> None:
    provider_router._AUDIO_ADAPTER_CACHE.clear()

    class _Eleven:
        pass

    class _Minimax:
        pass

    monkeypatch.setattr(provider_router, "ElevenLabsAudioProvider", _Eleven)
    monkeypatch.setattr(provider_router, "MinimaxAudioProvider", _Minimax)

    assert provider_router.normalize_audio_provider_name(None) == "elevenlabs"
    assert provider_router.normalize_audio_provider_name(" 11labs ") == "elevenlabs"
    assert provider_router.normalize_audio_provider_name("custom") == "custom"

    a1 = provider_router.get_audio_provider_adapter("11labs")
    a2 = provider_router.get_audio_provider_adapter("elevenlabs")
    m1 = provider_router.get_audio_provider_adapter("minimax")
    assert isinstance(a1, _Eleven)
    assert a1 is a2
    assert isinstance(m1, _Minimax)

    with pytest.raises(ValueError, match="Unsupported audio provider"):
        provider_router.get_audio_provider_adapter("unknown")

    assert provider_router.resolve_audio_provider(requested_provider="11labs", voice_provider="minimax") == "elevenlabs"
    assert provider_router.resolve_audio_provider(requested_provider=None, voice_provider="11labs") == "elevenlabs"
    assert provider_router.resolve_audio_provider(requested_provider=None, voice_provider=None, default_provider="minimax") == "minimax"


def test_project_repository_create_get_list_update(db_session) -> None:
    repo = ProjectRepository(db_session)
    user_id = uuid.uuid4()

    created = repo.create(ProjectCreate(title="Project A", description="desc"), user_id)
    fetched = repo.get(created.id)
    listed = repo.list()

    assert fetched is not None
    assert fetched.title == "Project A"
    assert any(item.id == created.id for item in listed)

    updated = repo.update(created.id, ProjectUpdate(title="Project B", status="active"))
    assert updated is not None
    assert updated.title == "Project B"
    assert updated.status == "active"

    missing = repo.update(uuid.uuid4(), ProjectUpdate(title="Nope"))
    assert missing is None


def test_voice_repository_list_get_update_with_filters(db_session) -> None:
    repo = VoiceRepository(db_session)
    v1 = Voice(
        id=uuid.uuid4(),
        name="Voice EN",
        source_type="system",
        language_code="en",
        visibility="public",
    )
    v2 = Voice(
        id=uuid.uuid4(),
        name="Voice VI",
        source_type="cloned",
        language_code="vi",
        visibility="private",
    )
    db_session.add_all([v1, v2])
    db_session.commit()

    all_rows = repo.list(VoiceListFilters())
    en_rows = repo.list(VoiceListFilters(language_code="en"))
    cloned_rows = repo.list(VoiceListFilters(source_type="cloned"))
    fetched = repo.get(v1.id)

    assert any(row.id == v1.id for row in all_rows)
    assert any(row.id == v1.id for row in en_rows)
    assert any(row.id == v2.id for row in cloned_rows)
    assert fetched is not None
    assert fetched.name == "Voice EN"

    updated = repo.update(v1.id, VoiceUpdate(name="Voice EN Updated", visibility="internal", metadata_json={"a": 1}))
    assert updated is not None
    assert updated.name == "Voice EN Updated"
    assert updated.visibility == "internal"
    assert updated.metadata_json == {"a": 1}

    missing = repo.update(uuid.uuid4(), VoiceUpdate(name="None"))
    assert missing is None