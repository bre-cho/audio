import pytest
from app.audio_engines.sound_effects.elevenlabs_sfx_adapter import ElevenLabsSFXAdapter
from app.audio_engines.bgm.replicate_musicgen_adapter import ReplicateMusicGenAdapter


def test_sfx_adapter_blocks_until_wired():
    with pytest.raises(NotImplementedError):
        ElevenLabsSFXAdapter().generate(prompt="boom", duration_sec=2, output_path="x.wav")


def test_bgm_adapter_blocks_until_wired():
    with pytest.raises(NotImplementedError):
        ReplicateMusicGenAdapter().generate(prompt="calm", duration_sec=10, loopable=True, output_path="x.wav")
