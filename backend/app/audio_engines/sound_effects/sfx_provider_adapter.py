from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratedSFX:
    path: str
    provider: str
    license: dict
    metadata: dict


class SFXProviderAdapter:
    def generate(self, *, prompt: str, duration_sec: float, output_path: str) -> GeneratedSFX:
        provider = os.getenv("SFX_PROVIDER", "disabled").lower()
        if provider in {"", "disabled", "none"}:
            raise RuntimeError("sfx_provider_disabled")
        raise RuntimeError(f"sfx_provider_not_wired:{provider}")
