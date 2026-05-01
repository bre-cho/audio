from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol


class Capability(str, Enum):
    TTS = "tts"
    VOICE_CLONE = "voice_clone"
    VOICE_CONVERSION = "voice_conversion"
    STT = "stt"
    SFX = "sfx"
    BGM = "bgm"
    PODCAST = "podcast"
    ENHANCER = "enhancer"
    NOISE_REDUCTION = "noise_reduction"


@dataclass(frozen=True)
class CapabilityState:
    capability: Capability
    status: str  # ready | partial | disabled | blocked | planned
    reason: str = ""
    provider: str = ""


class AudioProvider(Protocol):
    name: str

    def capability(self, capability: Capability) -> CapabilityState: ...

    async def run(self, capability: Capability, payload: dict[str, Any]) -> dict[str, Any]: ...
