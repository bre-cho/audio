from __future__ import annotations

from app.providers.elevenlabs_real import ElevenLabsRealProvider
from app.services.provider_capability_gate_v2 import require_capability


def clone_voice_real(*, name: str, sample_paths: list[str], description: str | None = None) -> dict:
    state = require_capability("voice_clone")
    if state.provider != "elevenlabs":
        raise RuntimeError(f"unsupported_clone_provider:{state.provider}")
    result = ElevenLabsRealProvider().clone_voice(name=name, sample_paths=sample_paths, description=description)
    return {"provider": result.provider, "external_voice_id": result.external_id, "metadata": result.metadata}
