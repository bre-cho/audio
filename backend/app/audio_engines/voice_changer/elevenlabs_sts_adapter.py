from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from app.providers.elevenlabs import ElevenLabsProvider
from app.providers.elevenlabs.schemas import SpeechToSpeechRequest
from app.services.audio_signal_validator import validate_audio_signal

# Allowed audio file extensions for input
_ALLOWED_INPUT_SUFFIXES = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".webm"}
# voice_id must be alphanumeric + hyphens only (ElevenLabs format)
_VOICE_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")


def _validate_input_path(input_path: str) -> Path:
    """Resolve and validate the input file path, preventing path traversal."""
    p = Path(input_path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"voice_changer_input_not_found: {p.name}")
    if p.stat().st_size == 0:
        raise ValueError("voice_changer_input_empty")
    if p.suffix.lower() not in _ALLOWED_INPUT_SUFFIXES:
        raise ValueError(f"voice_changer_input_unsupported_format: {p.suffix}")
    return p


def _validate_output_path(output_path: str) -> Path:
    """Resolve and prepare the output path, preventing path traversal."""
    p = Path(output_path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


@dataclass(frozen=True)
class VoiceConversionResult:
    output_path: str
    provider: str
    target_voice_id: str
    metadata: dict


class ElevenLabsVoiceChangerAdapter:
    """Voice conversion backed by ElevenLabs speech-to-speech endpoint.

    Requires ``ELEVENLABS_API_KEY`` and ``VOICE_CONVERSION_PROVIDER=elevenlabs``.
    """

    provider_name = "elevenlabs"

    def convert(
        self,
        *,
        input_path: str,
        target_voice_id: str,
        output_path: str,
        preserve_formants: bool = True,
    ) -> VoiceConversionResult:
        if not _VOICE_ID_RE.match(target_voice_id):
            raise ValueError("voice_changer_invalid_target_voice_id")

        src = _validate_input_path(input_path)
        out = _validate_output_path(output_path)

        audio_bytes = src.read_bytes()
        req = SpeechToSpeechRequest(
            audio_bytes=audio_bytes,
            filename=src.name,
            target_voice_id=target_voice_id,
        )
        result = ElevenLabsProvider().speech_to_speech(req)
        if not result.audio_bytes:
            raise RuntimeError("elevenlabs_speech_to_speech_returned_empty_audio")

        out.write_bytes(result.audio_bytes)

        signal = validate_audio_signal(str(out))
        if not signal.ok:
            raise RuntimeError(f"voice_changer_output_invalid:{signal.reason}")

        return VoiceConversionResult(
            output_path=str(out),
            provider=self.provider_name,
            target_voice_id=target_voice_id,
            metadata={"model_id": result.model_id},
        )
