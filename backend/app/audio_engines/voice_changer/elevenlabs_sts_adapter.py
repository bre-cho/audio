from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from app.services.audio_signal_validator import validate_audio_signal


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
        from app.providers.elevenlabs import ElevenLabsProvider
        from app.providers.elevenlabs.schemas import SpeechToSpeechRequest, VoiceSettings

        src = Path(input_path)
        if not src.exists() or src.stat().st_size == 0:
            raise ValueError("voice_changer_input_missing_or_empty")

        audio_bytes = src.read_bytes()
        req = SpeechToSpeechRequest(
            audio_bytes=audio_bytes,
            filename=src.name,
            target_voice_id=target_voice_id,
        )
        result = ElevenLabsProvider().speech_to_speech(req)
        if not result.audio_bytes:
            raise RuntimeError("elevenlabs_speech_to_speech_returned_empty_audio")

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
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
