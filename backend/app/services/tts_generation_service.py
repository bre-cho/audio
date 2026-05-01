from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.providers.elevenlabs import ElevenLabsProvider
from app.providers.minimax import MinimaxProvider
from app.services.audio_decode_service import decode_to_wav
from app.services.audio_signal_validator import validate_audio_signal
from app.services.provider_capability_gate_v2 import require_capability
from app.services.provider_cost_service import estimate_tts_cost


class TTSGenerationService:
    def generate(self, *, text: str, voice_id: str, output_dir: str = "artifacts/audio") -> dict:
        state = require_capability("tts")
        if state.provider == "elevenlabs":
            raw = ElevenLabsProvider().generate_speech({"text": text, "voice_id": voice_id})
        elif state.provider == "minimax":
            raw = MinimaxProvider().generate_speech({"text": text, "voice_id": voice_id, "output_format": "mp3"})
        else:
            raise RuntimeError(f"unsupported_tts_provider:{state.provider}")
        audio_bytes = raw.get("audio_bytes") or b""
        if not audio_bytes:
            raise RuntimeError("provider_returned_empty_audio")
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        mp3_path = out_dir / f"{uuid4()}.mp3"
        mp3_path.write_bytes(audio_bytes)
        wav_path = decode_to_wav(str(mp3_path))
        signal = validate_audio_signal(wav_path)
        return {
            "status": "completed",
            "provider": state.provider,
            "audio_path": str(mp3_path),
            "decoded_wav_path": wav_path,
            "signal_validation": signal,
            "cost_estimate": estimate_tts_cost(state.provider, text).dict(),
            "metadata": raw.get("metadata") or {},
        }
