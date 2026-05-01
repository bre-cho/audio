from __future__ import annotations

import mimetypes
import os
from pathlib import Path

from app.providers.elevenlabs import ElevenLabsProvider
from app.providers.elevenlabs.schemas import STTRequest


class STTService:
    def transcribe(self, audio_path: str, language: str = "auto") -> dict:
        provider = os.getenv("STT_PROVIDER", "disabled").strip().lower()
        if provider in {"", "disabled", "none"}:
            raise RuntimeError("stt_provider_disabled: set STT_PROVIDER=whisper or STT_PROVIDER=elevenlabs")
        if provider == "whisper":
            from app.audio_engines.stt.whisper_adapter import WhisperAdapter
            model_name = os.getenv("WHISPER_MODEL", "base")
            result = WhisperAdapter(model_name=model_name).transcribe(audio_path)
            return result.dict()
        if provider == "elevenlabs":
            p = Path(audio_path)
            if not p.exists() or p.stat().st_size == 0:
                raise ValueError("audio_file_missing_or_empty")
            audio_bytes = p.read_bytes()
            mime = mimetypes.guess_type(str(p))[0] or "audio/mpeg"
            req = STTRequest(
                audio_bytes=audio_bytes,
                filename=p.name,
                language_code=None if language in {"auto", ""} else language,
            )
            result = ElevenLabsProvider().speech_to_text(req)
            return {
                "text": result.text,
                "language": result.language_code,
                "segments": result.segments,
            }
        raise RuntimeError(f"unsupported_stt_provider:{provider}")
