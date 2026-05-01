from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

AudioFormat = Literal["mp3", "wav", "pcm", "flac"]


@dataclass(frozen=True)
class ProviderHealth:
    provider: str
    ok: bool
    status: str
    reason: str | None = None
    latency_ms: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MinimaxTTSRequest:
    text: str
    voice_id: str
    model: str = "speech-2.8-hd"
    audio_format: AudioFormat = "mp3"
    speed: float = 1.0
    volume: float = 1.0
    pitch: int = 0
    language_boost: str | None = None
    sample_rate: int | None = None
    bitrate: int | None = None


@dataclass(frozen=True)
class MinimaxAudioResult:
    audio_bytes: bytes
    audio_format: str
    provider: str
    model: str
    voice_id: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MinimaxAsyncTTSRequest:
    text: str
    voice_id: str
    model: str = "speech-2.8-hd"
    audio_format: AudioFormat = "mp3"


@dataclass(frozen=True)
class MinimaxAsyncTaskResult:
    task_id: str
    raw: dict[str, Any]


@dataclass(frozen=True)
class MinimaxAsyncTaskStatus:
    task_id: str
    status: str
    file_id: str | None = None
    download_url: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MinimaxFileUploadResult:
    file_id: str
    purpose: str
    raw: dict[str, Any]


@dataclass(frozen=True)
class MinimaxCloneRequest:
    voice_id: str
    clone_file_id: str
    clone_prompt: str | None = None
    prompt_file_id: str | None = None


@dataclass(frozen=True)
class MinimaxCloneResult:
    voice_id: str
    provider: str = "minimax"
    activation_required: bool = True
    expires_in_hours: int = 168
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MinimaxVoiceDesignRequest:
    prompt: str
    model: str = "speech-2.8-hd"


@dataclass(frozen=True)
class MinimaxVoiceDesignResult:
    voice_id: str
    trial_audio_bytes: bytes | None
    raw: dict[str, Any] = field(default_factory=dict)
