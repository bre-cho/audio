from __future__ import annotations

import logging

from app.core.runtime_guard import assert_real_provider
from app.services.audio.provider_base import BaseAudioProviderAdapter
from app.services.audio.providers.elevenlabs_provider import ElevenLabsAudioProvider
from app.services.audio.providers.minimax_provider import MinimaxAudioProvider

logger = logging.getLogger(__name__)
_AUDIO_ADAPTER_CACHE: dict[str, BaseAudioProviderAdapter] = {}
_AUDIO_PROVIDER_ALIASES: dict[str, str] = {
    "elevenlabs": "elevenlabs",
    "11labs": "elevenlabs",
    "minimax": "minimax",
}


def normalize_audio_provider_name(provider: str | None) -> str:
    normalized = str(provider or "elevenlabs").strip().lower()
    return _AUDIO_PROVIDER_ALIASES.get(normalized, normalized)


def get_audio_provider_adapter(provider: str | None) -> BaseAudioProviderAdapter:
    provider_key = normalize_audio_provider_name(provider)
    if provider_key in _AUDIO_ADAPTER_CACHE:
        return _AUDIO_ADAPTER_CACHE[provider_key]

    if provider_key == "elevenlabs":
        adapter: BaseAudioProviderAdapter = ElevenLabsAudioProvider()
    elif provider_key == "minimax":
        adapter = MinimaxAudioProvider()
    else:
        raise ValueError(f"Unsupported audio provider: {provider}")

    _AUDIO_ADAPTER_CACHE[provider_key] = adapter
    return adapter


def resolve_audio_provider(*, requested_provider: str | None, voice_provider: str | None = None, default_provider: str = "elevenlabs") -> str:
    feature = "audio_provider_resolve"
    if requested_provider:
        resolved = normalize_audio_provider_name(requested_provider)
        assert_real_provider(resolved, feature=feature)
        return resolved
    if voice_provider:
        resolved = normalize_audio_provider_name(voice_provider)
        assert_real_provider(resolved, feature=feature)
        return resolved
    resolved = normalize_audio_provider_name(default_provider)
    assert_real_provider(resolved, feature=feature)
    return resolved
