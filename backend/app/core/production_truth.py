from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class RuntimeTruthStatus(str, Enum):
    READY = "ready"
    PARTIAL = "partial"
    DISABLED = "disabled"
    BLOCKED = "blocked"
    PLANNED = "planned"


BLOCKED_PROVIDER_NAMES = {"internal_genvoice", "mock", "stub", "placeholder", "silent_wav"}


@dataclass(frozen=True)
class RuntimeTruthDecision:
    allowed: bool
    status: RuntimeTruthStatus
    reason: str
    provider: str | None = None
    capability: str | None = None


def current_env() -> str:
    return os.getenv("APP_ENV", os.getenv("ENV", "development")).lower()


def is_production_like() -> bool:
    return current_env() in {"prod", "production", "staging", "stage"}


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def assert_runtime_truth(provider: str | None, capability: str, *, allowed_providers: Iterable[str] | None = None) -> RuntimeTruthDecision:
    provider_name = (provider or "").strip().lower()
    strict = env_bool("PROVIDER_STRICT_MODE", True)
    block_internal = env_bool("BLOCK_INTERNAL_GENVOICE_IN_PROD", True)
    allow_placeholder = env_bool("ALLOW_PLACEHOLDER_AUDIO", False)

    if not provider_name:
        return RuntimeTruthDecision(False, RuntimeTruthStatus.BLOCKED, "provider_missing", provider, capability)

    if allowed_providers is not None and provider_name not in {p.lower() for p in allowed_providers}:
        return RuntimeTruthDecision(False, RuntimeTruthStatus.BLOCKED, "provider_not_allowed_for_capability", provider, capability)

    if is_production_like() and block_internal and provider_name in BLOCKED_PROVIDER_NAMES:
        return RuntimeTruthDecision(False, RuntimeTruthStatus.BLOCKED, "placeholder_provider_blocked_in_production", provider, capability)

    if strict and not allow_placeholder and provider_name in BLOCKED_PROVIDER_NAMES:
        return RuntimeTruthDecision(False, RuntimeTruthStatus.BLOCKED, "placeholder_provider_blocked_by_strict_mode", provider, capability)

    return RuntimeTruthDecision(True, RuntimeTruthStatus.READY, "provider_allowed", provider, capability)
