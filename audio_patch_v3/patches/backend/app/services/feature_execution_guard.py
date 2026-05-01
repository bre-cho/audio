from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from fastapi import HTTPException, status

from app.services.provider_capability_gate_v2 import get_capability_state


@dataclass(frozen=True)
class FeatureExecutionState:
    capability: str
    provider: str | None
    status: str
    reason: str
    sync_supported: bool = False
    async_supported: bool = False

    def dict(self) -> dict[str, Any]:
        return asdict(self)


def assert_capability_ready(capability: str) -> FeatureExecutionState:
    state = get_capability_state(capability)
    if state.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "capability_not_ready",
                "capability": capability,
                "provider": state.provider,
                "status": state.status,
                "reason": state.reason,
            },
        )
    return FeatureExecutionState(
        capability=capability,
        provider=state.provider,
        status=state.status,
        reason=state.reason,
    )


def not_implemented(capability: str, provider: str | None, reason: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error": "engine_not_implemented",
            "capability": capability,
            "provider": provider,
            "reason": reason,
        },
    )
