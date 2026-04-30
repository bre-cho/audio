from __future__ import annotations

from app.core.config import settings
from app.providers.capability_registry import get_capability


def can_fallback(*, requested_provider: str, fallback_provider: str, capability: str) -> tuple[bool, str]:
    if not bool(getattr(settings, "allow_provider_fallback", False)):
        return False, "ALLOW_PROVIDER_FALLBACK=false"

    requested = get_capability(requested_provider)
    fallback = get_capability(fallback_provider)

    if not getattr(requested, capability, False):
        return False, f"requested provider '{requested_provider}' does not support {capability}"
    if not getattr(fallback, capability, False):
        return False, f"fallback provider '{fallback_provider}' does not support {capability}"
    if not fallback.production_ready:
        return False, f"fallback provider '{fallback_provider}' is not production_ready"
    if requested_provider == "elevenlabs" and fallback_provider == "internal_genvoice":
        return False, "fallback from elevenlabs to internal_genvoice is forbidden"

    return True, "ok"
