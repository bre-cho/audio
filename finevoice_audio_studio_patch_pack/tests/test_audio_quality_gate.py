import wave
from pathlib import Path
from backend.app.services.audio_quality_gate import AudioQualityGate


def test_silent_wav_rejected(tmp_path: Path):
    p = tmp_path / 'silent.wav'
    with wave.open(str(p), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b'\x00\x00' * 16000)
    result = AudioQualityGate().inspect_wav(p)
    assert result.qa_pass is False
    assert result.silence_detected is True
