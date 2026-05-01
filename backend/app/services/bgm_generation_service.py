from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from app.services.provider_capability_gate_v2 import require_capability


class BGMPrompt(BaseModel):
    prompt: str = Field(min_length=3)
    duration_sec: float = Field(default=30, ge=2, le=600)
    mood: str = "cinematic"
    loopable: bool = True


class BGMGenerationService:
    def generate(self, payload: BGMPrompt, output_dir: str = "artifacts/bgm") -> dict:
        require_capability("bgm")
        from app.services.provider_runtime import load_provider_adapter
        adapter = load_provider_adapter("bgm")
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = str(out_dir / f"{uuid4().hex}.wav")
        result = adapter.generate(
            prompt=f"{payload.prompt} mood:{payload.mood}",
            duration_sec=payload.duration_sec,
            loopable=payload.loopable,
            output_path=out_path,
        )
        return {
            "status": "completed",
            "provider": result.provider,
            "audio_path": result.output_path,
            "prompt": result.prompt,
            "duration_sec": result.duration_sec,
            "loopable": result.loopable,
            "license": result.license,
        }
