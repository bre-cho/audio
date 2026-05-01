from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratedBGM:
    path: str
    provider: str
    license: dict
    metadata: dict


class BGMProviderAdapter:
    """Dispatch BGM generation to the configured provider backend.

    Supported providers (set ``BGM_PROVIDER`` env var):
    - ``replicate_musicgen`` — Meta MusicGen via Replicate API (requires ``REPLICATE_API_TOKEN``)
    """

    def generate(self, *, prompt: str, duration_sec: float, loopable: bool, output_path: str) -> GeneratedBGM:
        provider = os.getenv("BGM_PROVIDER", "disabled").lower()
        if provider in {"", "disabled", "none"}:
            raise RuntimeError(
                "bgm_provider_disabled: set BGM_PROVIDER=replicate_musicgen and REPLICATE_API_TOKEN"
            )
        if provider == "replicate_musicgen":
            from app.audio_engines.bgm.replicate_musicgen_adapter import ReplicateMusicGenAdapter
            result = ReplicateMusicGenAdapter().generate(
                prompt=prompt,
                duration_sec=duration_sec,
                loopable=loopable,
                output_path=output_path,
            )
            return GeneratedBGM(
                path=result.output_path,
                provider=result.provider,
                license=result.license,
                metadata={
                    "prompt": result.prompt,
                    "duration_sec": result.duration_sec,
                    "loopable": result.loopable,
                },
            )
        raise RuntimeError(
            f"bgm_provider_not_supported:{provider} — "
            "supported values: replicate_musicgen"
        )
