from __future__ import annotations

from pathlib import Path
from app.services.audio_signal_validator import validate_audio_signal


def validate_voice_conversion_output(output_path: str) -> dict:
    p = Path(output_path)
    if not p.exists() or p.stat().st_size == 0:
        raise RuntimeError("voice_conversion_output_missing_or_empty")
    signal = validate_audio_signal(str(p))
    return {"signal": signal, "quality_gate_pass": True}
