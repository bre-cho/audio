from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ProviderCapability:
    provider: str
    tts: bool = False
    voice_clone: bool = False
    voice_conversion: bool = False
    voice_design: bool = False
    sound_effect: bool = False
    noise_reduction: bool = False
    voice_enhancement: bool = False
    podcast_mix: bool = False
    production_ready: bool = False
    status: str = "disabled"
    reason: str | None = None


CAPABILITIES: dict[str, ProviderCapability] = {
    "elevenlabs": ProviderCapability(
        provider="elevenlabs",
        tts=True,
        voice_clone=True,
        voice_conversion=False,
        voice_design=True,
        sound_effect=True,
        noise_reduction=False,
        voice_enhancement=False,
        podcast_mix=False,
        production_ready=True,
        status="active",
        reason=None,
    ),
    "minimax": ProviderCapability(
        provider="minimax",
        tts=False,
        voice_clone=False,
        production_ready=False,
        status="disabled",
        reason="Provider mapping chua hoan thien production",
    ),
    "internal_genvoice": ProviderCapability(
        provider="internal_genvoice",
        tts=True,
        production_ready=False,
        status="placeholder",
        reason="Chi dung cho dev/test, khong duoc phep production",
    ),
}


def get_capability(provider: str) -> ProviderCapability:
    caps = CAPABILITIES.get(provider)
    if not caps:
        raise ValueError(f"Unknown provider: {provider}")
    return caps


def require_capability(provider: str, capability: str) -> ProviderCapability:
    caps = get_capability(provider)
    if not getattr(caps, capability, False):
        raise ValueError(f"Provider '{provider}' does not support capability '{capability}'")
    return caps


def as_dict(provider: str) -> dict:
    return asdict(get_capability(provider))


# Engine-level capabilities (provider-agnostic, implemented in audio_engines/)
ENGINE_CAPABILITIES: dict[str, dict] = {
    "noise_reduction": {
        "status": "active",
        "algorithm": "frame_rms_gate",
        "provider_required": False,
        "note": "Pure-Python spectral noise gate",
    },
    "voice_enhancement": {
        "status": "active",
        "presets": ["clean", "broadcast", "podcast"],
        "provider_required": False,
        "note": "IIR high-pass + normalize + compress chain",
    },
    "podcast_mix": {
        "status": "active",
        "provider_required": False,
        "note": "Multi-segment WAV mixer with crossfade",
    },
    "voice_design": {"status": "planned", "provider_required": True},
    "sound_effects": {"status": "disabled", "provider_required": True},
    "voice_changer": {"status": "disabled", "provider_required": True},
}
