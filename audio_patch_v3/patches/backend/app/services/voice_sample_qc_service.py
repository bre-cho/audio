from __future__ import annotations

from pathlib import Path
import wave


class VoiceSampleQCError(RuntimeError):
    pass


def inspect_wav_duration(path: str) -> float:
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        raise VoiceSampleQCError("sample_missing_or_empty")
    with wave.open(str(p), "rb") as wf:
        return wf.getnframes() / float(wf.getframerate())


def validate_clone_samples(sample_paths: list[str], min_total_sec: float = 30.0, max_total_sec: float = 1800.0) -> dict:
    if not sample_paths:
        raise VoiceSampleQCError("no_clone_samples")
    durations = []
    for path in sample_paths:
        if path.lower().endswith(".wav"):
            durations.append(inspect_wav_duration(path))
        else:
            if not Path(path).exists() or Path(path).stat().st_size == 0:
                raise VoiceSampleQCError("sample_missing_or_empty")
            durations.append(0.0)
    total = sum(durations)
    if total and total < min_total_sec:
        raise VoiceSampleQCError(f"clone_sample_too_short:{total:.2f}s")
    if total > max_total_sec:
        raise VoiceSampleQCError(f"clone_sample_too_long:{total:.2f}s")
    return {"sample_count": len(sample_paths), "total_duration_sec": total, "qc_pass": True}
