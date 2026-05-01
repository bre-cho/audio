from dataclasses import dataclass
from pathlib import Path


@dataclass
class VoiceConversionRequest:
    input_path: Path
    target_voice_id: str
    provider: str
    preserve_formant: bool = True


@dataclass
class VoiceConversionResult:
    output_path: Path
    similarity_score: float
    naturalness_score: float
    artifact_score: float
    provider_model: str


class RealVoiceConversionAdapter:
    name = "base"

    def is_configured(self) -> bool:
        return False

    async def convert(self, request: VoiceConversionRequest) -> VoiceConversionResult:
        raise NotImplementedError("Wire RVC/OpenVoice/provider runtime before enabling voice conversion.")
