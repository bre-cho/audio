from __future__ import annotations

import math
import wave
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudioSignalReport:
    ok: bool
    duration_sec: float
    rms: float
    peak: float
    silence_ratio: float
    reason: str


def _read_wav_mono_float(path: Path) -> tuple[list[float], int]:
    with wave.open(str(path), "rb") as wf:
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
    if sample_width != 2:
        raise ValueError("only_16bit_pcm_wav_supported_by_lightweight_validator")
    values: list[float] = []
    for i in range(0, len(frames), sample_width * channels):
        # first channel only for validation
        sample = int.from_bytes(frames[i:i + 2], "little", signed=True)
        values.append(sample / 32768.0)
    return values, rate


def validate_audio_signal(path: str | Path, *, min_rms: float = 0.001, max_silence_ratio: float = 0.98) -> AudioSignalReport:
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return AudioSignalReport(False, 0.0, 0.0, 0.0, 1.0, "file_missing_or_empty")
    try:
        samples, rate = _read_wav_mono_float(p)
    except Exception as exc:
        return AudioSignalReport(False, 0.0, 0.0, 0.0, 1.0, f"invalid_wav:{exc}")
    if not samples or rate <= 0:
        return AudioSignalReport(False, 0.0, 0.0, 0.0, 1.0, "no_samples")
    duration = len(samples) / float(rate)
    rms = math.sqrt(sum(s * s for s in samples) / len(samples))
    peak = max(abs(s) for s in samples)
    silent = sum(1 for s in samples if abs(s) < min_rms)
    silence_ratio = silent / len(samples)
    if duration <= 0:
        return AudioSignalReport(False, duration, rms, peak, silence_ratio, "zero_duration")
    if rms < min_rms:
        return AudioSignalReport(False, duration, rms, peak, silence_ratio, "rms_below_threshold")
    if silence_ratio > max_silence_ratio:
        return AudioSignalReport(False, duration, rms, peak, silence_ratio, "silence_ratio_too_high")
    return AudioSignalReport(True, duration, rms, peak, silence_ratio, "ok")
