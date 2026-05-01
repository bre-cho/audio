from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class VoiceConversionResult:
    output_path: str
    similarity_score: float
    naturalness_score: float
    artifact_score: float
    clipping_detected: bool
    silence_detected: bool

    def to_dict(self):
        return asdict(self)


class VoiceConversionEngine:
    """Scaffold. Replace passthrough with RVC/so-vits-svc/provider conversion."""

    def convert(self, input_path: str, target_voice_id: str, output_path: str) -> VoiceConversionResult:
        raise NotImplementedError("Wire real voice conversion provider/model before enabling production route")
