from dataclasses import dataclass
from pathlib import Path


@dataclass
class SFXRequest:
    prompt: str
    duration_sec: float
    provider: str
    seed: int | None = None
    commercial_use: bool = True


@dataclass
class SFXResult:
    output_path: Path
    provider_model: str
    license: str
    duration_sec: float
    seed: int | None = None


class SFXProviderAdapterV4:
    name = "base"

    def is_configured(self) -> bool:
        return False

    async def generate(self, request: SFXRequest) -> SFXResult:
        raise NotImplementedError("Wire real SFX endpoint before enabling.")
