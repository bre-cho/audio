from fastapi import HTTPException
from app.providers.provider_contract import AudioProvider, Capability, CapabilityState


class ProviderRegistryV4:
    def __init__(self) -> None:
        self._providers: dict[str, AudioProvider] = {}

    def register(self, provider: AudioProvider) -> None:
        if provider.name in self._providers:
            raise RuntimeError(f"duplicate provider registered: {provider.name}")
        self._providers[provider.name] = provider

    def capability_matrix(self) -> list[CapabilityState]:
        states: list[CapabilityState] = []
        for provider in self._providers.values():
            for cap in Capability:
                states.append(provider.capability(cap))
        return states

    def require(self, provider_name: str, capability: Capability) -> AudioProvider:
        provider = self._providers.get(provider_name)
        if not provider:
            raise HTTPException(409, {"error": "provider_not_registered", "provider": provider_name})
        state = provider.capability(capability)
        if state.status != "ready":
            raise HTTPException(409, {
                "error": "capability_not_ready",
                "provider": provider_name,
                "capability": capability.value,
                "status": state.status,
                "reason": state.reason,
            })
        return provider


registry_v4 = ProviderRegistryV4()
