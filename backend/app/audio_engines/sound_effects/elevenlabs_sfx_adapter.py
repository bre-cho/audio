"""Deprecated scaffold: enable only through single-source ProviderRegistryV4 wiring."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SFXResult:
    output_path: str
    provider: str
    prompt: str
    metadata: dict


class ElevenLabsSFXAdapter:
    provider_name = "elevenlabs"

    def generate(self, *, prompt: str, duration_sec: float, output_path: str, **kwargs) -> SFXResult:
        raise NotImplementedError("Wire ElevenLabs text-to-sound-effects endpoint and validate non-empty output before enabling SFX_PROVIDER=elevenlabs")
