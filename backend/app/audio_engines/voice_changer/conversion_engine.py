from __future__ import annotations


def convert_voice(*, source_artifact_id: str, mode: str, target_voice_id: str | None = None) -> dict:
    return {
        "status": "disabled",
        "reason": "Production conversion engine not wired",
        "mode": mode,
        "source_artifact_id": source_artifact_id,
        "target_voice_id": target_voice_id,
    }
