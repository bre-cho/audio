from app.services.provider_capability_gate_v2 import get_capability_state


def test_disabled_capability(monkeypatch):
    monkeypatch.setenv("SFX_PROVIDER", "disabled")
    state = get_capability_state("sound_effects")
    assert state.status == "disabled"


def test_missing_api_key_blocks(monkeypatch):
    monkeypatch.setenv("TTS_PROVIDER", "elevenlabs")
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    state = get_capability_state("tts")
    assert state.status == "blocked"
