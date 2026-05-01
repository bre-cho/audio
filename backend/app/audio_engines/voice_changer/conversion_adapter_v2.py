from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceConversionResult:
    output_path: str
    provider: str
    metadata: dict


class VoiceConversionAdapterV2:
    def convert(self, *, input_path: str, target_voice_id: str, output_path: str) -> VoiceConversionResult:
        provider = os.getenv("VOICE_CONVERSION_PROVIDER", "disabled").lower()
        if provider in {"", "disabled", "none"}:
            raise RuntimeError("voice_conversion_provider_disabled")
        if provider == "rvc_local":
            raise RuntimeError("rvc_local_not_wired: add model path + inference command")
        if provider == "openvoice_local":
            raise RuntimeError("openvoice_local_not_wired: add checkpoint path + inference command")
        raise RuntimeError(f"unsupported_voice_conversion_provider:{provider}")
