from dataclasses import dataclass
from pathlib import Path


@dataclass
class BGMRequest:
    prompt: str
    duration_sec: float
    provider: str
    loopable: bool = False
    seed: int | None = None
    commercial_use: bool = True


@dataclass
class BGMResult:
    output_path: Path
    provider_model: str
    license: str
    duration_sec: float
    loopable: bool
    seed: int | None = None


class BGMProviderAdapterV4:
    name = "base"

    def is_configured(self) -> bool:
        return False

    async def generate(self, request: BGMRequest) -> BGMResult:
        raise NotImplementedError("Wire real BGM/music endpoint before enabling.")
