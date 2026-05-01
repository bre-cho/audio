from __future__ import annotations

from app.services.provider_runtime import load_provider_adapter
from app.services.voice_conversion_quality_gate import validate_voice_conversion_output


class VoiceConversionJobService:
    def convert(self, payload: dict) -> dict:
        input_path = payload.get("input_path")
        if not input_path:
            raise NotImplementedError("artifact_storage_lookup_for_input_artifact_id_not_wired")
        adapter = load_provider_adapter("voice_changer")
        result = adapter.convert(
            input_path=input_path,
            target_voice_id=payload["target_voice_id"],
            output_path=payload.get("output_path", "artifacts/voice_changer/converted.wav"),
            preserve_formants=payload.get("preserve_formants", True),
        )
        qa = validate_voice_conversion_output(result.output_path)
        return {"status": "completed", **result.__dict__, "qa": qa}
