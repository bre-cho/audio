import pytest
from app.audio_engines.sound_effects.elevenlabs_sfx_adapter import ElevenLabsSFXAdapter
from app.audio_engines.bgm.replicate_musicgen_adapter import ReplicateMusicGenAdapter


def test_sfx_adapter_blocks_until_wired():
    with pytest.raises(NotImplementedError):
        ElevenLabsSFXAdapter().generate(prompt="boom", duration_sec=2, output_path="x.wav")


def test_bgm_adapter_requires_api_token():
    """ReplicateMusicGenAdapter is now wired; it raises RuntimeError when the
    REPLICATE_API_TOKEN env var is absent, not NotImplementedError."""
    with pytest.raises(RuntimeError, match="missing_replicate_api_token"):
        ReplicateMusicGenAdapter().generate(prompt="calm", duration_sec=10, loopable=True, output_path="x.wav")
