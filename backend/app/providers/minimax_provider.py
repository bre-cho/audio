from __future__ import annotations

from pathlib import Path
from typing import Any

from .minimax_client import MinimaxClient
from .minimax_models import (
    MinimaxAsyncTTSRequest,
    MinimaxCloneRequest,
    MinimaxTTSRequest,
    MinimaxVoiceDesignRequest,
    ProviderHealth,
)


class MinimaxProvider:
    """Canonical Minimax provider adapter.

    This replaces old scaffold adapters that raised NotImplementedError.
    Keep this as the single source of truth and make legacy modules import this class.
    """

    name = "minimax"

    def __init__(self, settings: Any) -> None:
        self.settings = settings
        self.client = MinimaxClient(
            api_key=settings.minimax_api_key,
            base_url=getattr(settings, "minimax_base_url", "https://api.minimax.io"),
            group_id=getattr(settings, "minimax_group_id", None),
            timeout_seconds=float(getattr(settings, "minimax_timeout_seconds", 60)),
            connect_timeout_seconds=float(getattr(settings, "minimax_connect_timeout_seconds", 10)),
        )

    def health_check(self) -> ProviderHealth:
        return self.client.health_check()

    def require_capability(self, capability: str) -> None:
        health = self.health_check()
        if not health.ok:
            raise RuntimeError(f"minimax capability {capability} unavailable: {health.reason}")
        flag_name = f"minimax_enable_{capability}"
        if hasattr(self.settings, flag_name) and not bool(getattr(self.settings, flag_name)):
            raise RuntimeError(f"minimax capability {capability} disabled by config")

    def synthesize_speech(self, *, text: str, voice_id: str | None = None, model: str | None = None, audio_format: str = "mp3", **kwargs: Any):
        self.require_capability("tts")
        request = MinimaxTTSRequest(
            text=text,
            voice_id=voice_id or getattr(self.settings, "minimax_default_voice_id", "male-qn-qingse"),
            model=model or getattr(self.settings, "minimax_default_tts_model", "speech-2.8-hd"),
            audio_format=audio_format,  # type: ignore[arg-type]
            speed=float(kwargs.get("speed", 1.0)),
            volume=float(kwargs.get("volume", 1.0)),
            pitch=int(kwargs.get("pitch", 0)),
            language_boost=kwargs.get("language_boost"),
        )
        return self.client.synthesize_speech(request)

    def create_async_tts_task(self, *, text: str, voice_id: str | None = None, model: str | None = None, audio_format: str = "mp3"):
        self.require_capability("async_tts")
        return self.client.create_async_tts_task(
            MinimaxAsyncTTSRequest(
                text=text,
                voice_id=voice_id or getattr(self.settings, "minimax_default_voice_id", "male-qn-qingse"),
                model=model or getattr(self.settings, "minimax_default_tts_model", "speech-2.8-hd"),
                audio_format=audio_format,  # type: ignore[arg-type]
            )
        )

    def query_async_tts_task(self, task_id: str):
        self.require_capability("async_tts")
        return self.client.query_async_tts_task(task_id)

    def upload_voice_clone_audio(self, path: str | Path):
        self.require_capability("voice_clone")
        return self.client.upload_file(path, purpose="voice_clone")

    def upload_prompt_audio(self, path: str | Path):
        self.require_capability("voice_clone")
        return self.client.upload_file(path, purpose="prompt_audio")

    def clone_voice(self, *, voice_id: str, clone_file_id: str, clone_prompt: str | None = None, prompt_file_id: str | None = None):
        self.require_capability("voice_clone")
        return self.client.clone_voice(
            MinimaxCloneRequest(
                voice_id=voice_id,
                clone_file_id=clone_file_id,
                clone_prompt=clone_prompt,
                prompt_file_id=prompt_file_id,
            )
        )

    def design_voice(self, *, prompt: str, model: str | None = None):
        self.require_capability("voice_design")
        return self.client.design_voice(
            MinimaxVoiceDesignRequest(
                prompt=prompt,
                model=model or getattr(self.settings, "minimax_default_tts_model", "speech-2.8-hd"),
            )
        )

    def list_voices(self, voice_type: str = "all") -> dict[str, Any]:
        self.require_capability("voice_management")
        return self.client.list_voices(voice_type=voice_type)

    def delete_voice(self, voice_id: str) -> dict[str, Any]:
        self.require_capability("voice_management")
        return self.client.delete_voice(voice_id)
