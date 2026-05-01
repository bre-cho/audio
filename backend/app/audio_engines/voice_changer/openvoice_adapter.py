from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceConversionResult:
    output_path: str
    provider: str
    target_voice_id: str
    metadata: dict


class OpenVoiceConversionAdapter:
    provider_name = "openvoice"

    def convert(self, *, input_path: str, target_voice_id: str, output_path: str, preserve_formants: bool = True) -> VoiceConversionResult:
        raise NotImplementedError(
            "OpenVoice adapter scaffold only. Wire tone color converter, speaker embedding extraction, checkpoint loading, and QA before enabling."
        )
