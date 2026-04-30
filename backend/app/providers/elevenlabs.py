from __future__ import annotations

import logging
import mimetypes

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
        api_key = self._api_key()
        if not api_key:
            raise RuntimeError("ElevenLabs API key is missing for clone flow")

        name = str(payload.get("name") or "").strip()
        if not name:
            raise ValueError("clone voice requires non-empty name")

        sample_files = payload.get("sample_files") or []
        if not sample_files:
            raise ValueError("clone voice requires at least one sample file")

        multipart_files = []
        for index, sample in enumerate(sample_files):
            filename = sample.get("filename") or f"sample-{index + 1}.wav"
            content = sample.get("content") or b""
            content_type = sample.get("content_type") or mimetypes.guess_type(filename)[0] or "audio/wav"
            if not isinstance(content, (bytes, bytearray)) or len(content) == 0:
                raise ValueError("clone sample content must be non-empty bytes")
            multipart_files.append(("files", (filename, bytes(content), content_type)))

        remove_background_noise = bool(payload.get("remove_background_noise", True))
        form_data = {
            "name": name,
            "remove_background_noise": "true" if remove_background_noise else "false",
        }

        try:
            import httpx

            resp = httpx.post(
                f"{_ELEVENLABS_BASE_URL}/voices/add",
                headers={"xi-api-key": api_key},
                data=form_data,
                files=multipart_files,
                timeout=60,
            )
            resp.raise_for_status()
            body = resp.json()
            voice_id = body.get("voice_id")
            if not voice_id:
                raise RuntimeError(f"ElevenLabs clone response missing voice_id: {body}")
            return {
                "status": "ok",
                "provider": self.code,
                "voice_id": str(voice_id),
                "raw": body,
            }
        except Exception as exc:
            logger.error("ElevenLabs clone_voice failed: %s", exc)
            raise RuntimeError(f"ElevenLabs clone failed: {exc}") from exc
