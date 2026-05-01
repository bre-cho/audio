from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class ProviderCostEstimate:
    provider: str
    capability: str
    unit: str
    quantity: float
    estimated_cost_usd: float | None = None

    def dict(self) -> dict:
        return asdict(self)


def estimate_tts_cost(provider: str, text: str) -> ProviderCostEstimate:
    return ProviderCostEstimate(provider=provider, capability="tts", unit="characters", quantity=float(len(text)))
