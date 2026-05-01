from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderBinding:
    capability: str
    provider: str
    adapter_path: str
    requires_api_key_env: str | None = None


SUPPORTED_BINDINGS: dict[tuple[str, str], ProviderBinding] = {
    ("tts", "elevenlabs"): ProviderBinding("tts", "elevenlabs", "app.providers.elevenlabs_real.ElevenLabsRealProvider", "ELEVENLABS_API_KEY"),
    ("voice_clone", "elevenlabs"): ProviderBinding("voice_clone", "elevenlabs", "app.providers.elevenlabs_real.ElevenLabsRealProvider", "ELEVENLABS_API_KEY"),
    ("tts", "minimax"): ProviderBinding("tts", "minimax", "app.providers.minimax.MinimaxProvider", "MINIMAX_API_KEY"),
    ("voice_clone", "minimax"): ProviderBinding("voice_clone", "minimax", "app.providers.minimax.MinimaxProvider", "MINIMAX_API_KEY"),
    ("stt", "whisper"): ProviderBinding("stt", "whisper", "app.audio_engines.stt.whisper_adapter.WhisperAdapter", None),
    ("voice_changer", "rvc"): ProviderBinding("voice_changer", "rvc", "app.audio_engines.voice_changer.rvc_adapter.RVCVoiceConversionAdapter", None),
    ("voice_changer", "openvoice"): ProviderBinding("voice_changer", "openvoice", "app.audio_engines.voice_changer.openvoice_adapter.OpenVoiceConversionAdapter", None),
    ("sound_effects", "elevenlabs"): ProviderBinding("sound_effects", "elevenlabs", "app.audio_engines.sound_effects.elevenlabs_sfx_adapter.ElevenLabsSFXAdapter", "ELEVENLABS_API_KEY"),
    ("bgm", "replicate_musicgen"): ProviderBinding("bgm", "replicate_musicgen", "app.audio_engines.bgm.replicate_musicgen_adapter.ReplicateMusicGenAdapter", "REPLICATE_API_TOKEN"),
}


def _provider_env_name(capability: str) -> str:
    return {
        "tts": "TTS_PROVIDER",
        "voice_clone": "VOICE_CLONE_PROVIDER",
        "voice_changer": "VOICE_CONVERSION_PROVIDER",
        "sound_effects": "SFX_PROVIDER",
        "bgm": "BGM_PROVIDER",
        "stt": "STT_PROVIDER",
    }.get(capability, f"{capability.upper()}_PROVIDER")


def resolve_provider(capability: str, provider: str | None = None) -> ProviderBinding:
    provider_name = provider or os.getenv(_provider_env_name(capability), "disabled")
    key = (capability, provider_name)
    if key not in SUPPORTED_BINDINGS:
        raise RuntimeError(f"provider_binding_not_supported:{capability}:{provider_name}")
    binding = SUPPORTED_BINDINGS[key]
    if binding.requires_api_key_env and not os.getenv(binding.requires_api_key_env):
        raise RuntimeError(f"missing_provider_api_key:{binding.requires_api_key_env}")
    return binding
