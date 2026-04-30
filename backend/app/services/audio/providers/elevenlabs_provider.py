from __future__ import annotations

from app.providers.elevenlabs import ElevenLabsProvider
from app.services.audio.provider_base import (
    AudioCloneResult,
    AudioProviderVoice,
    AudioSynthesisResult,
    BaseAudioProviderAdapter,
)


class ElevenLabsAudioProvider(BaseAudioProviderAdapter):
    provider_name = "elevenlabs"

    def __init__(self) -> None:
        self._provider = ElevenLabsProvider()

    async def list_voices(self) -> list[AudioProviderVoice]:
        raw_voices = self._provider.list_voices()
        voices: list[AudioProviderVoice] = []
        for item in raw_voices:
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
        result = self._provider.generate_speech(
            {"voice_id": voice_id, "text": text, "model_id": model_id, "output_format": output_format or "mp3_44100_128"}
        )
        audio_bytes: bytes = result.get("audio_bytes") or b""
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
        sample_files = []
        if options:
            sample_files = options.get("sample_files") or []
        result = self._provider.clone_voice(
            {
                "name": name,
                "files": files,
                "sample_files": sample_files,
                "remove_background_noise": remove_background_noise,
            }
        )
        if result.get("status") not in ("failed", "error") and result.get("voice_id"):
            return AudioCloneResult(
                provider=self.provider_name,
                provider_voice_id=result.get("voice_id"),
                status="ready",
                raw=result,
            )
        return AudioCloneResult(
            provider=self.provider_name,
            provider_voice_id=None,
            status="failed",
            raw=result,
            error_message=str(result.get("error") or "clone_failed"),
        )

    async def compose_music(
        self,
        *,
        prompt_text: str | None = None,
        duration_seconds: int = 30,
        force_instrumental: bool = True,
        options: dict | None = None,
    ) -> AudioSynthesisResult:
        result = self._provider.generate_speech(
            {"prompt_text": prompt_text, "duration_seconds": duration_seconds, "force_instrumental": force_instrumental}
        )
        audio_bytes: bytes = result.get("audio_bytes") or b""
        return AudioSynthesisResult(
            provider=self.provider_name,
            audio_bytes=audio_bytes,
            content_type="audio/mpeg",
            output_format="mp3",
        )
