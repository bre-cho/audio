from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.providers.minimax_provider import MinimaxProvider


@dataclass(frozen=True)
class CapabilityState:
    provider: str
    capability: str
    status: str
    reason: str


def get_minimax_capabilities(settings: Any) -> list[CapabilityState]:
    if not getattr(settings, "minimax_api_key", None):
        return [
            CapabilityState("minimax", "tts", "blocked", "missing_api_key"),
            CapabilityState("minimax", "async_tts", "blocked", "missing_api_key"),
            CapabilityState("minimax", "voice_clone", "blocked", "missing_api_key"),
            CapabilityState("minimax", "voice_design", "blocked", "missing_api_key"),
            CapabilityState("minimax", "voice_management", "blocked", "missing_api_key"),
        ]

    provider = MinimaxProvider(settings)
    health = provider.health_check()
    if not health.ok:
        return [
            CapabilityState("minimax", "tts", "blocked", health.reason or "health_failed"),
            CapabilityState("minimax", "async_tts", "blocked", health.reason or "health_failed"),
            CapabilityState("minimax", "voice_clone", "blocked", health.reason or "health_failed"),
            CapabilityState("minimax", "voice_design", "blocked", health.reason or "health_failed"),
            CapabilityState("minimax", "voice_management", "blocked", health.reason or "health_failed"),
        ]

    def flag(name: str) -> bool:
        return bool(getattr(settings, f"minimax_enable_{name}", False))

    return [
        CapabilityState("minimax", "tts", "ready" if flag("tts") else "partial", "health_ok" if flag("tts") else "disabled_by_config"),
        CapabilityState("minimax", "async_tts", "ready" if flag("async_tts") else "partial", "health_ok" if flag("async_tts") else "disabled_by_config"),
        CapabilityState("minimax", "voice_clone", "ready" if flag("voice_clone") else "partial", "health_ok" if flag("voice_clone") else "disabled_by_config"),
        CapabilityState("minimax", "voice_design", "ready" if flag("voice_design") else "partial", "health_ok" if flag("voice_design") else "disabled_by_config"),
        CapabilityState("minimax", "voice_management", "ready" if flag("voice_management") else "partial", "health_ok" if flag("voice_management") else "disabled_by_config"),
    ]
