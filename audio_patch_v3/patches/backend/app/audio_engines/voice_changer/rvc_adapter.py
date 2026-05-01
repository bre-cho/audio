from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceConversionResult:
    output_path: str
    provider: str
    target_voice_id: str
    metadata: dict


class RVCVoiceConversionAdapter:
    provider_name = "rvc"

    def convert(self, *, input_path: str, target_voice_id: str, output_path: str, preserve_formants: bool = True) -> VoiceConversionResult:
        raise NotImplementedError(
            "RVC adapter scaffold only. Wire model checkpoint, index file, F0 extraction, infer pipeline, and artifact validation before enabling VOICE_CONVERSION_PROVIDER=rvc."
        )
