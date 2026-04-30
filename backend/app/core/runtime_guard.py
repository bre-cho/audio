from __future__ import annotations

from app.core.config import settings

PLACEHOLDER_PROVIDERS = {"internal_genvoice", "mock", "stub", "placeholder"}


class RuntimeGuardError(RuntimeError):
    pass


def is_production_like() -> bool:
    env = (settings.app_env or "dev").strip().lower()
    return env in {"production", "prod", "staging"} or bool(settings.provider_strict_mode)


def assert_real_provider(provider: str, feature: str) -> None:
    if is_production_like() and provider in PLACEHOLDER_PROVIDERS:
        raise RuntimeGuardError(
            f"Blocked placeholder provider '{provider}' for feature '{feature}' in production-like runtime"
        )