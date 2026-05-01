from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from app.services.provider_capability_gate_v2 import require_capability


class SFXPrompt(BaseModel):
    prompt: str = Field(min_length=3)
    duration_sec: float = Field(default=4, ge=0.5, le=30)
    style: str = "cinematic"
    loopable: bool = False


class SFXGenerationService:
    def generate(self, payload: SFXPrompt, output_dir: str = "artifacts/sfx") -> dict:
        state = require_capability("sound_effects")
        if state.provider == "elevenlabs":
            from app.providers.elevenlabs import ElevenLabsProvider
            result = ElevenLabsProvider().generate_sound_effect(
                payload.prompt,
                duration_seconds=payload.duration_sec,
            )
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            artifact_id = uuid4().hex
            out_path = out_dir / f"{artifact_id}.mp3"
            out_path.write_bytes(result.audio_bytes)
            return {
                "status": "completed",
                "provider": state.provider,
                "artifact_id": artifact_id,
                "audio_path": str(out_path),
                "prompt": payload.prompt,
                "duration_sec": payload.duration_sec,
                "metadata": result.metadata,
            }
        raise RuntimeError(f"unsupported_sfx_provider:{state.provider}")
