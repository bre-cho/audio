from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.providers.elevenlabs_real import ElevenLabsRealProvider
from app.services.provider_capability_gate_v2 import require_capability
from app.services.audio_signal_validator import validate_audio_signal


def synthesize_tts_to_file(*, text: str, voice_id: str, output_dir: str = "artifacts/audio") -> dict:
    state = require_capability("tts")
    if state.provider != "elevenlabs":
        raise RuntimeError(f"unsupported_tts_provider:{state.provider}")
    result = ElevenLabsRealProvider().text_to_speech(text=text, voice_id=voice_id)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # ElevenLabs often returns MP3; write raw provider extension for ffmpeg conversion stage.
    path = out_dir / f"{uuid4()}.mp3"
    path.write_bytes(result.audio_bytes or b"")
    return {"path": str(path), "provider": result.provider, "metadata": result.metadata, "signal_validation": "requires_decode_to_wav"}
