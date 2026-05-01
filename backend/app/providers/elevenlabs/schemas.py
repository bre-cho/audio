from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, BinaryIO, Iterator, Optional

@dataclass
class VoiceSettings:
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    speed: float = 1.0
    use_speaker_boost: bool = True

    def to_payload(self) -> dict[str, Any]:
        return {
            "stability": self.stability,
            "similarity_boost": self.similarity_boost,
            "style": self.style,
            "speed": self.speed,
            "use_speaker_boost": self.use_speaker_boost,
        }

@dataclass
class TTSRequest:
    text: str
    voice_id: str
    model_id: str = "eleven_multilingual_v2"
    output_format: str = "mp3_44100_128"
    voice_settings: VoiceSettings = field(default_factory=VoiceSettings)

@dataclass
class AudioResult:
    audio_bytes: bytes
    content_type: str
    provider: str = "elevenlabs"
    model_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class CloneVoiceRequest:
    name: str
    files: list[tuple[str, bytes, str]]
    description: Optional[str] = None
    labels: dict[str, str] = field(default_factory=dict)
    remove_background_noise: bool = True
    consent_proof: Optional[str] = None

@dataclass
class CloneVoiceResult:
    voice_id: str
    requires_verification: bool
    provider: str = "elevenlabs"
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class SpeechToSpeechRequest:
    audio_bytes: bytes
    filename: str
    target_voice_id: str
    model_id: str = "eleven_multilingual_sts_v2"
    output_format: str = "mp3_44100_128"
    voice_settings: VoiceSettings = field(default_factory=VoiceSettings)

@dataclass
class STTRequest:
    audio_bytes: bytes
    filename: str
    model_id: str = "scribe_v1"
    language_code: Optional[str] = None
    diarize: bool = False

@dataclass
class TranscriptResult:
    text: str
    segments: list[dict[str, Any]] = field(default_factory=list)
    language_code: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ProviderHealth:
    provider: str
    status: str
    message: str
    capabilities: dict[str, bool]
    usage: dict[str, Any] = field(default_factory=dict)
