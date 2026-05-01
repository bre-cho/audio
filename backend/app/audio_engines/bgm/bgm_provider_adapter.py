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
    def generate(self, *, prompt: str, duration_sec: float, loopable: bool, output_path: str) -> GeneratedBGM:
        provider = os.getenv("BGM_PROVIDER", "disabled").lower()
        if provider in {"", "disabled", "none"}:
            raise RuntimeError("bgm_provider_disabled")
        raise RuntimeError(f"bgm_provider_not_wired:{provider}")
