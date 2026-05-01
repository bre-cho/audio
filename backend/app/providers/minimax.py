from __future__ import annotations

from app.core.config import settings
from app.providers.base import BaseTTSProvider
from app.providers.minimax_provider import MinimaxProvider as _CanonicalMinimaxProvider


class MinimaxProvider(BaseTTSProvider):
    code = 'minimax'

    def __init__(self) -> None:
        self._provider = _CanonicalMinimaxProvider(settings)

    def list_voices(self, filters: dict | None = None) -> list[dict]:
        voice_type = 'all'
        if filters and isinstance(filters.get('voice_type'), str):
            voice_type = str(filters['voice_type'])
        payload = self._provider.list_voices(voice_type=voice_type)
        voices = payload.get('voices')
        return voices if isinstance(voices, list) else []

    def generate_speech(self, payload: dict) -> dict:
        result = self._provider.synthesize_speech(
            text=str(payload.get('text') or ''),
            voice_id=payload.get('voice_id'),
            model=payload.get('model_id') or payload.get('model'),
            audio_format=str(payload.get('output_format') or 'mp3'),
            speed=payload.get('speed', 1.0),
            volume=payload.get('volume', 1.0),
            pitch=payload.get('pitch', 0),
        )
        return {
            'status': 'ok',
            'provider': self.code,
            'audio_bytes': result.audio_bytes,
            'mime_type': 'audio/mpeg' if result.audio_format == 'mp3' else 'audio/wav',
            'metadata': result.raw,
        }

    def clone_voice(self, payload: dict) -> dict:
        result = self._provider.clone_voice(
            voice_id=str(payload.get('voice_id') or ''),
            clone_file_id=str(payload.get('clone_file_id') or ''),
            clone_prompt=payload.get('clone_prompt'),
            prompt_file_id=payload.get('prompt_file_id'),
        )
        return {
            'status': 'ok',
            'provider': self.code,
            'voice_id': result.voice_id,
            'activation_required': result.activation_required,
            'raw': result.raw,
        }
