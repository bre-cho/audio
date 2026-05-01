from __future__ import annotations

from app.core.config import settings
from app.providers.minimax_provider import MinimaxProvider
from app.services.audio.provider_base import (
    AudioCloneResult,
    AudioProviderVoice,
    AudioSynthesisResult,
    BaseAudioProviderAdapter,
)


class MinimaxAudioProvider(BaseAudioProviderAdapter):
    provider_name = "minimax"

    def __init__(self) -> None:
        self._provider = MinimaxProvider(settings)

    async def list_voices(self) -> list[AudioProviderVoice]:
        raw = self._provider.list_voices(voice_type="all")
        voices = raw.get("voices") if isinstance(raw, dict) else []
        if not isinstance(voices, list):
            return []
        output: list[AudioProviderVoice] = []
        for item in voices:
            if not isinstance(item, dict):
                continue
            voice_id = str(item.get("voice_id") or item.get("id") or "").strip()
            if not voice_id:
                continue
            output.append(
                AudioProviderVoice(
                    provider=self.provider_name,
                    voice_id=voice_id,
                    display_name=str(item.get("name") or voice_id),
                    raw=item,
                )
            )
        return output

    async def synthesize_speech(
        self,
        *,
        voice_id: str,
        text: str,
        model_id: str | None = None,
        output_format: str | None = None,
        options: dict | None = None,
    ) -> AudioSynthesisResult:
        result = self._provider.synthesize_speech(
            text=text,
            voice_id=voice_id,
            model=model_id,
            audio_format=output_format or "mp3",
            **(options or {}),
        )
        return AudioSynthesisResult(
            provider=self.provider_name,
            audio_bytes=result.audio_bytes,
            content_type="audio/mpeg" if result.audio_format == "mp3" else "audio/wav",
            output_format=result.audio_format,
            raw=result.raw,
        )

    async def clone_voice(
        self,
        *,
        name: str,
        files: list[str],
        remove_background_noise: bool = True,
        options: dict | None = None,
    ) -> AudioCloneResult:
        clone_file_id = ""
        prompt_file_id = None
        clone_prompt = None
        if options:
            clone_file_id = str(options.get("clone_file_id") or "")
            prompt_file_id = options.get("prompt_file_id")
            clone_prompt = options.get("clone_prompt")
        result = self._provider.clone_voice(
            voice_id=name,
            clone_file_id=clone_file_id,
            clone_prompt=clone_prompt,
            prompt_file_id=prompt_file_id,
        )
        return AudioCloneResult(
            provider=self.provider_name,
            provider_voice_id=result.voice_id,
            status="pending_verification" if result.activation_required else "ready",
            raw=result.raw,
        )
