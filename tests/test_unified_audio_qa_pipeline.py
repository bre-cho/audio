import wave
from pathlib import Path
from app.services.unified_audio_qa_pipeline import UnifiedAudioQAPipeline


def test_rejects_silent_wav(tmp_path: Path):
    p = tmp_path / "silent.wav"
    with wave.open(str(p), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 16000)
    result = UnifiedAudioQAPipeline().validate_wav(p)
    assert not result.passed
    assert result.silence_detected
