from __future__ import annotations


def generate_sfx(*, prompt: str, duration_sec: int = 5) -> dict:
    return {
        "status": "disabled",
        "reason": "Provider-backed SFX generation is not wired",
        "prompt": prompt,
        "duration_sec": duration_sec,
    }
