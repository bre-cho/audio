from __future__ import annotations

import io
import math
import struct
import wave
from dataclasses import dataclass


@dataclass
class AudioSignalReport:
    passed: bool
    duration_ms: int
    rms: int
    peak: int
    reason: str | None = None


def _pcm_stats(frames: bytes, sample_width: int) -> tuple[int, int]:
    if not frames:
        return 0, 0

    if sample_width == 1:
        samples = [byte - 128 for byte in frames]
    elif sample_width == 2:
        count = len(frames) // 2
        samples = struct.unpack(f"<{count}h", frames[: count * 2])
    else:
        raise ValueError(f"unsupported_sample_width:{sample_width}")

    peak = max(abs(int(sample)) for sample in samples)
    rms = int(math.sqrt(sum(int(sample) * int(sample) for sample in samples) / len(samples)))
    return rms, peak


def validate_wav_signal(data: bytes, min_duration_ms: int = 300, min_rms: int = 20) -> AudioSignalReport:
    try:
        with wave.open(io.BytesIO(data), "rb") as wav:
            frames = wav.readframes(wav.getnframes())
            rate = wav.getframerate()
            width = wav.getsampwidth()
            duration_ms = int((wav.getnframes() / rate) * 1000) if rate else 0
            rms, peak = _pcm_stats(frames, width)
    except Exception as exc:
        return AudioSignalReport(False, 0, 0, 0, f"invalid_wav:{exc}")

    if duration_ms < min_duration_ms:
        return AudioSignalReport(False, duration_ms, rms, peak, "duration_too_short")
    if rms < min_rms:
        return AudioSignalReport(False, duration_ms, rms, peak, "silent_or_near_silent")
    return AudioSignalReport(True, duration_ms, rms, peak, None)