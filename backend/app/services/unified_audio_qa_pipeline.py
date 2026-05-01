import math
import struct
from dataclasses import dataclass
from pathlib import Path
import wave


@dataclass
class AudioQAResult:
    passed: bool
    duration_sec: float
    rms: float
    peak: int
    clipping_detected: bool
    silence_detected: bool
    reason: str = ""


def _compute_rms_peak(frames: bytes, sample_width: int) -> tuple[float, int]:
    """Compute RMS and peak amplitude without audioop (Python 3.13+ safe)."""
    if not frames:
        return 0.0, 0
    if sample_width == 1:
        # unsigned 8-bit PCM
        samples = struct.unpack(f"{len(frames)}B", frames)
        centered = [s - 128 for s in samples]
        peak_val = max(abs(s) for s in centered)
        rms_val = math.sqrt(sum(s * s for s in centered) / len(centered))
    elif sample_width == 2:
        count = len(frames) // 2
        samples = struct.unpack(f"<{count}h", frames[: count * 2])
        peak_val = max(abs(s) for s in samples)
        rms_val = math.sqrt(sum(s * s for s in samples) / len(samples))
    elif sample_width == 3:
        # 24-bit PCM — unpack complete 3-byte samples only
        samples = []
        for i in range(0, (len(frames) // 3) * 3, 3):
            val = int.from_bytes(frames[i : i + 3], "little", signed=True)
            samples.append(val)
        if not samples:
            return 0.0, 0
        peak_val = max(abs(s) for s in samples)
        rms_val = math.sqrt(sum(s * s for s in samples) / len(samples))
    elif sample_width == 4:
        count = len(frames) // 4
        samples = struct.unpack(f"<{count}i", frames[: count * 4])
        peak_val = max(abs(s) for s in samples)
        rms_val = math.sqrt(sum(s * s for s in samples) / len(samples))
    else:
        return 0.0, 0
    return rms_val, int(peak_val)


class UnifiedAudioQAPipeline:
    """Single validation path for all generated/imported audio artifacts.

    Pure-Python implementation (no audioop dependency) — compatible with
    Python 3.12 and 3.13+.  Extend with pyloudnorm / ffmpeg probes for
    LUFS and SNR measurements in production.
    """

    def validate_wav(self, path: str | Path, min_duration_sec: float = 0.2) -> AudioQAResult:
        p = Path(path)
        if not p.exists() or p.stat().st_size == 0:
            return AudioQAResult(False, 0, 0, 0, False, True, "missing_or_empty_file")
        try:
            with wave.open(str(p), "rb") as wf:
                frames = wf.readframes(wf.getnframes())
                rate = wf.getframerate() or 1
                width = wf.getsampwidth()
                nframes = wf.getnframes()
                duration = nframes / rate
        except Exception as exc:
            return AudioQAResult(False, 0, 0, 0, False, True, f"decode_failed:{exc}")

        rms, peak = _compute_rms_peak(frames, width)
        max_val = (2 ** (8 * width - 1) - 1) if width > 1 else 127
        clipping = peak >= (max_val - 2)
        silence = rms < 10

        if duration < min_duration_sec:
            return AudioQAResult(False, duration, rms, peak, clipping, silence, "duration_too_short")
        if silence:
            return AudioQAResult(False, duration, rms, peak, clipping, silence, "silence_detected")
        if clipping:
            return AudioQAResult(False, duration, rms, peak, clipping, silence, "clipping_detected")
        return AudioQAResult(True, duration, rms, peak, clipping, silence)
