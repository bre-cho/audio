from __future__ import annotations

from app.services.audio.elevenlabs_adapter import ElevenLabsAdapter
from app.services.audio.provider_base import (
    AudioCloneResult,
    AudioProviderVoice,
    AudioSynthesisResult,
    BaseAudioProviderAdapter,
)


class ElevenLabsAudioProvider(BaseAudioProviderAdapter):
    provider_name = "elevenlabs"

    def __init__(self) -> None:
        self.adapter = ElevenLabsAdapter()

    async def list_voices(self) -> list[AudioProviderVoice]:
        result = await self.adapter.list_voices()
        if not result.get("ok"):
            return []
        body = result.get("body") or {}
        items = body.get("voices") or body.get("shared_voices") or []
        voices: list[AudioProviderVoice] = []
        for item in items:
            voice_id = item.get("voice_id") or item.get("shared_voice_id")
            if not voice_id:
                continue
            voices.append(
                AudioProviderVoice(
                    provider=self.provider_name,
                    voice_id=voice_id,
                    display_name=item.get("name") or voice_id,
                    language_code=(item.get("labels") or {}).get("language"),
                    gender=(item.get("labels") or {}).get("gender"),
                    preview_url=item.get("preview_url"),
                    raw=item,
                )
            )
        return voices

    async def synthesize_speech(
        self,
        *,
        voice_id: str,
        text: str,
        model_id: str | None = None,
        output_format: str | None = None,
        options: dict | None = None,
    ) -> AudioSynthesisResult:
        audio_bytes = await self.adapter.synthesize_speech(
            voice_id=voice_id,
            text=text,
            model_id=model_id,
            output_format=output_format or "mp3_44100_128",
        )
        return AudioSynthesisResult(
            provider=self.provider_name,
            audio_bytes=audio_bytes,
            content_type="audio/mpeg",
            output_format=output_format or "mp3_44100_128",
        )

    async def clone_voice(
        self,
        *,
        name: str,
        files: list[str],
        remove_background_noise: bool = True,
        options: dict | None = None,
    ) -> AudioCloneResult:
        result = await self.adapter.create_ivc_voice(
            name=name,
            files=files,
            remove_background_noise=remove_background_noise,
        )
        if result.get("ok"):
            body = result.get("body") or {}
            return AudioCloneResult(
                provider=self.provider_name,
                provider_voice_id=body.get("voice_id"),
                status="ready",
                raw=body,
            )
        return AudioCloneResult(
            provider=self.provider_name,
            provider_voice_id=None,
            status="failed",
            raw=result,
            error_message=str(result.get("body") or result.get("status_code") or "clone_failed"),
        )

    async def compose_music(
        self,
        *,
        prompt_text: str | None = None,
        duration_seconds: int = 30,
        force_instrumental: bool = True,
        options: dict | None = None,
    ) -> AudioSynthesisResult:
        music_bytes = await self.adapter.compose_music(
            prompt_text=prompt_text,
            duration_seconds=duration_seconds,
            force_instrumental=force_instrumental,
        )
        return AudioSynthesisResult(
            provider=self.provider_name,
            audio_bytes=music_bytes,
            content_type="audio/mpeg",
            output_format="mp3",
        )
