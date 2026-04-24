from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AudioProviderVoice:
    provider: str
    voice_id: str
    display_name: str
    language_code: str | None = None
    gender: str | None = None
    preview_url: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AudioSynthesisResult:
    provider: str
    audio_bytes: bytes
    content_type: str = "audio/mpeg"
    output_format: str | None = None
    estimated_duration_ms: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AudioCloneResult:
    provider: str
    provider_voice_id: str | None
    status: str
    raw: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None


class BaseAudioProviderAdapter(ABC):
    provider_name: str

    @abstractmethod
    async def list_voices(self) -> list[AudioProviderVoice]:
        raise NotImplementedError

    @abstractmethod
    async def synthesize_speech(
        self,
        *,
        voice_id: str,
        text: str,
        model_id: str | None = None,
        output_format: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> AudioSynthesisResult:
        raise NotImplementedError

    @abstractmethod
    async def clone_voice(
        self,
        *,
        name: str,
        files: list[str],
        remove_background_noise: bool = True,
        options: dict[str, Any] | None = None,
    ) -> AudioCloneResult:
        raise NotImplementedError

    async def compose_music(
        self,
        *,
        prompt_text: str | None = None,
        duration_seconds: int = 30,
        force_instrumental: bool = True,
        options: dict[str, Any] | None = None,
    ) -> AudioSynthesisResult:
        raise NotImplementedError(f"{self.provider_name} does not support compose_music")
