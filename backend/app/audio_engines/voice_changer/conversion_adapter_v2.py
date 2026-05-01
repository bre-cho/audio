from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class VoiceConversionResult:
    output_path: str
    provider: str
    metadata: dict


class VoiceConversionAdapterV2:
    def convert(self, *, input_path: str, target_voice_id: str, output_path: str) -> VoiceConversionResult:
        provider = os.getenv("VOICE_CONVERSION_PROVIDER", "disabled").lower()
        if provider in {"", "disabled", "none"}:
            raise RuntimeError("voice_conversion_provider_disabled: set VOICE_CONVERSION_PROVIDER")
        if provider == "elevenlabs":
            from app.audio_engines.voice_changer.elevenlabs_sts_adapter import ElevenLabsVoiceChangerAdapter
            r = ElevenLabsVoiceChangerAdapter().convert(
                input_path=input_path,
                target_voice_id=target_voice_id,
                output_path=output_path,
            )
            return VoiceConversionResult(output_path=r.output_path, provider=r.provider, metadata=r.metadata)
        if provider == "rvc":
            from app.audio_engines.voice_changer.rvc_adapter import RVCVoiceConversionAdapter
            r = RVCVoiceConversionAdapter().convert(
                input_path=input_path,
                target_voice_id=target_voice_id,
                output_path=output_path,
            )
            return VoiceConversionResult(output_path=r.output_path, provider=r.provider, metadata=r.metadata)
        if provider == "openvoice":
            from app.audio_engines.voice_changer.openvoice_adapter import OpenVoiceConversionAdapter
            r = OpenVoiceConversionAdapter().convert(
                input_path=input_path,
                target_voice_id=target_voice_id,
                output_path=output_path,
            )
            return VoiceConversionResult(output_path=r.output_path, provider=r.provider, metadata=r.metadata)
        raise RuntimeError(f"unsupported_voice_conversion_provider:{provider}")
