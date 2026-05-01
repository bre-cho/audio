from __future__ import annotations

from app.services.audio_signal_validator import validate_audio_signal


def audio_quality_metrics(path: str) -> dict:
    report = validate_audio_signal(path)
    return {
        "ok": report.ok,
        "duration_sec": report.duration_sec,
        "rms": report.rms,
        "peak": report.peak,
        "silence_ratio": report.silence_ratio,
        "reason": report.reason,
        "clipping_detected": report.peak >= 0.999,
    }
