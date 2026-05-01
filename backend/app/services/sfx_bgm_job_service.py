from __future__ import annotations

from app.services.provider_runtime import load_provider_adapter
from app.services.audio_signal_validator import validate_audio_signal


class SFXBGMJobService:
    def generate_sfx(self, payload: dict) -> dict:
        adapter = load_provider_adapter("sound_effects")
        result = adapter.generate(**payload)
        qa = validate_audio_signal(result.output_path)
        return {"status": "completed", **result.__dict__, "qa": qa}

    def generate_bgm(self, payload: dict) -> dict:
        adapter = load_provider_adapter("bgm")
        result = adapter.generate(**payload)
        qa = validate_audio_signal(result.output_path)
        return {"status": "completed", **result.__dict__, "qa": qa}
