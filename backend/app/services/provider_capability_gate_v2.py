from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from typing import Literal

CapabilityStatus = Literal["ready", "partial", "disabled", "blocked", "planned"]


@dataclass(frozen=True)
class CapabilityState:
    capability: str
    status: CapabilityStatus
    provider: str | None
    reason: str
    requires_api_key: bool = False

    def dict(self) -> dict:
        return asdict(self)


CAPABILITY_ENV = {
    "tts": ("TTS_PROVIDER", "ELEVENLABS_API_KEY"),
    "voice_clone": ("VOICE_CLONE_PROVIDER", "ELEVENLABS_API_KEY"),
    "voice_translation": ("VOICE_TRANSLATION_PROVIDER", None),
    "voice_changer": ("VOICE_CONVERSION_PROVIDER", None),
    "stt": ("STT_PROVIDER", None),
    "sound_effects": ("SFX_PROVIDER", None),
    "bgm": ("BGM_PROVIDER", None),
    "podcast": ("PODCAST_PROVIDER", None),
    "audio_quality": ("AUDIO_QA_PROVIDER", None),
}

DISABLED_VALUES = {"", "disabled", "none", "planned", "stub", "mock", "placeholder"}


def get_capability_state(capability: str) -> CapabilityState:
    provider_env, key_env = CAPABILITY_ENV.get(capability, (None, None))
    if not provider_env:
        return CapabilityState(capability, "planned", None, "capability_not_registered")
    provider = os.getenv(provider_env, "disabled").strip()
    if provider.lower() in DISABLED_VALUES:
        return CapabilityState(capability, "disabled", provider, f"{provider_env}_disabled")
    if key_env and not os.getenv(key_env):
        return CapabilityState(capability, "blocked", provider, f"missing_{key_env.lower()}", True)
    return CapabilityState(capability, "ready", provider, "ready", bool(key_env))


def capability_matrix() -> dict[str, dict]:
    return {cap: get_capability_state(cap).dict() for cap in CAPABILITY_ENV}


def require_capability(capability: str) -> CapabilityState:
    state = get_capability_state(capability)
    if state.status != "ready":
        raise RuntimeError(f"capability_not_ready:{capability}:{state.status}:{state.reason}")
    return state
