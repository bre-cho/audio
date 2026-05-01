from dataclasses import dataclass
from pathlib import Path
import wave
import audioop


@dataclass
class AudioQAResult:
    passed: bool
    duration_sec: float
    rms: float
    peak: int
    clipping_detected: bool
    silence_detected: bool
    reason: str = ""


class UnifiedAudioQAPipeline:
    """Single validation path for all generated/imported audio artifacts.

    This implementation is dependency-light. Replace/extend with pyloudnorm,
    ffmpeg probes, SNR, VAD, and artifact scoring in production.
    """

    def validate_wav(self, path: str | Path, min_duration_sec: float = 0.2) -> AudioQAResult:
        p = Path(path)
        if not p.exists() or p.stat().st_size == 0:
            return AudioQAResult(False, 0, 0, 0, False, True, "missing_or_empty_file")
        try:
            with wave.open(str(p), "rb") as wf:
                frames = wf.readframes(wf.getnframes())
                rate = wf.getframerate() or 1
                channels = wf.getnchannels() or 1
                width = wf.getsampwidth()
                duration = wf.getnframes() / rate
                rms = float(audioop.rms(frames, width)) if frames else 0.0
                peak = int(audioop.max(frames, width)) if frames else 0
                clipping = peak >= (2 ** (8 * width - 1) - 2)
                silence = rms < 10
        except Exception as exc:
            return AudioQAResult(False, 0, 0, 0, False, True, f"decode_failed:{exc}")
        if duration < min_duration_sec:
            return AudioQAResult(False, duration, rms, peak, clipping, silence, "duration_too_short")
        if silence:
            return AudioQAResult(False, duration, rms, peak, clipping, silence, "silence_detected")
        if clipping:
            return AudioQAResult(False, duration, rms, peak, clipping, silence, "clipping_detected")
        return AudioQAResult(True, duration, rms, peak, clipping, silence)
