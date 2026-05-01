import wave
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict


@dataclass(frozen=True)
class AudioQAResult:
    duration_sec: float
    rms: float
    peak: float
    clipping_detected: bool
    silence_detected: bool
    qa_pass: bool
    reason: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


class AudioQualityGate:
    def __init__(self, min_duration_sec: float = 0.25, min_rms: float = 0.001, clipping_peak: float = 0.99) -> None:
        self.min_duration_sec = min_duration_sec
        self.min_rms = min_rms
        self.clipping_peak = clipping_peak

    def inspect_wav(self, path: str | Path) -> AudioQAResult:
        p = Path(path)
        if not p.exists() or p.stat().st_size <= 44:
            return AudioQAResult(0, 0, 0, False, True, False, "file_missing_or_empty")
        try:
            with wave.open(str(p), "rb") as wf:
                frames = wf.readframes(wf.getnframes())
                sample_width = wf.getsampwidth()
                framerate = wf.getframerate()
                nframes = wf.getnframes()
        except Exception as exc:
            return AudioQAResult(0, 0, 0, False, True, False, f"invalid_wav:{exc}")

        duration = nframes / float(framerate or 1)
        if sample_width != 2:
            return AudioQAResult(duration, 0, 0, False, True, False, "unsupported_sample_width")

        import struct, math
        count = len(frames) // 2
        if count == 0:
            return AudioQAResult(duration, 0, 0, False, True, False, "no_samples")
        samples = struct.unpack("<" + "h" * count, frames)
        norm = [s / 32768.0 for s in samples]
        rms = math.sqrt(sum(x * x for x in norm) / len(norm))
        peak = max(abs(x) for x in norm)
        silence = rms < self.min_rms
        clipping = peak >= self.clipping_peak
        passed = duration >= self.min_duration_sec and not silence and not clipping
        reason = "ok" if passed else "duration_or_silence_or_clipping_failed"
        return AudioQAResult(duration, rms, peak, clipping, silence, passed, reason)
