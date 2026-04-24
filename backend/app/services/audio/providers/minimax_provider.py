from __future__ import annotations

from app.services.audio.provider_base import (
    AudioCloneResult,
    AudioProviderVoice,
    AudioSynthesisResult,
    BaseAudioProviderAdapter,
)


class MinimaxAudioProvider(BaseAudioProviderAdapter):
    """
    Skeleton adapter.

    TODO:
    - map credentials from config
    - implement list_voices / clone_voice / synthesize endpoints
    - normalize Minimax response payloads về contract của BaseAudioProviderAdapter
    """

    provider_name = "minimax"

    async def list_voices(self) -> list[AudioProviderVoice]:
        return []

    async def synthesize_speech(
        self,
        *,
        voice_id: str,
        text: str,
        model_id: str | None = None,
        output_format: str | None = None,
        options: dict | None = None,
    ) -> AudioSynthesisResult:
        raise NotImplementedError("Minimax synthesize mapping is not implemented yet")

    async def clone_voice(
        self,
        *,
        name: str,
        files: list[str],
        remove_background_noise: bool = True,
        options: dict | None = None,
    ) -> AudioCloneResult:
        raise NotImplementedError("Minimax clone mapping is not implemented yet")
