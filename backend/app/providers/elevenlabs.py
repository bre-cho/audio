from __future__ import annotations

import logging

from app.core.config import settings
from app.providers.base import BaseTTSProvider

logger = logging.getLogger(__name__)

_ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
_DEFAULT_MODEL = "eleven_monolingual_v1"
_DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel


class ElevenLabsProvider(BaseTTSProvider):
    code = 'elevenlabs'

    def _api_key(self) -> str | None:
        return settings.elevenlabs_api_key

    def list_voices(self, filters: dict | None = None) -> list[dict]:
        api_key = self._api_key()
        if not api_key:
            return []
        try:
            import httpx
            resp = httpx.get(
                f"{_ELEVENLABS_BASE_URL}/voices",
                headers={"xi-api-key": api_key},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("voices", [])
        except Exception as exc:
            logger.warning("ElevenLabs list_voices failed: %s", exc)
            return []

    def generate_speech(self, payload: dict) -> dict:
        api_key = self._api_key()
        if not api_key:
            return {'status': 'queued', 'provider': self.code, 'audio_bytes': None}

        voice_id = payload.get("voice_id") or _DEFAULT_VOICE_ID
        text = payload.get("text") or ""
        model_id = payload.get("model_id") or _DEFAULT_MODEL
        output_format = payload.get("output_format") or "mp3_44100_128"

        try:
            import httpx
            resp = httpx.post(
                f"{_ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": api_key,
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "model_id": model_id,
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                },
                params={"output_format": output_format},
                timeout=30,
            )
            resp.raise_for_status()
            return {'status': 'ok', 'provider': self.code, 'audio_bytes': resp.content, 'mime_type': 'audio/mpeg'}
        except Exception as exc:
            logger.error("ElevenLabs generate_speech failed: %s", exc)
            raise RuntimeError(f"ElevenLabs TTS failed: {exc}") from exc

    def clone_voice(self, payload: dict) -> dict:
        return {'status': 'queued', 'provider': self.code}
