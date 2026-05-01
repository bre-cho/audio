from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BGMResult:
    output_path: str
    provider: str
    prompt: str
    duration_sec: float
    loopable: bool
    license: dict


class ReplicateMusicGenAdapter:
    provider_name = "replicate_musicgen"

    def generate(self, *, prompt: str, duration_sec: float, loopable: bool, output_path: str, **kwargs) -> BGMResult:
        raise NotImplementedError("Wire Replicate/MusicGen provider and commercial license metadata before enabling BGM_PROVIDER=replicate_musicgen")
