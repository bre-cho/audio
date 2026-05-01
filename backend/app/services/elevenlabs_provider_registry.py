"""
Apply idea:
- Import this provider into the existing unified provider registry.
- Remove/deprecate old duplicate ElevenLabs adapters.
"""
from app.providers.elevenlabs import ElevenLabsProvider

_PROVIDER_CACHE = {}

def get_elevenlabs_provider() -> ElevenLabsProvider:
    if "elevenlabs" not in _PROVIDER_CACHE:
        _PROVIDER_CACHE["elevenlabs"] = ElevenLabsProvider()
    return _PROVIDER_CACHE["elevenlabs"]


def require_elevenlabs_capability(capability: str) -> ElevenLabsProvider:
    provider = get_elevenlabs_provider()
    health = provider.health_check()
    if health.status != "ok" or not health.capabilities.get(capability, False):
        raise RuntimeError(f"elevenlabs_capability_not_ready:{capability}:{health.message}")
    return provider
