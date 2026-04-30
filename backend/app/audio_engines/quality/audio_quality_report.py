from __future__ import annotations


def build_quality_report(*, duration_ms: int, rms: int, peak: int, sample_rate: int | None = None, channels: int | None = None) -> dict:
    return {
        "duration_ms": duration_ms,
        "rms": rms,
        "peak": peak,
        "sample_rate": sample_rate,
        "channels": channels,
        "status": "basic",
    }
