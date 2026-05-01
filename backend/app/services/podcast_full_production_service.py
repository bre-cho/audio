from dataclasses import dataclass
from pathlib import Path


@dataclass
class PodcastSegment:
    speaker: str
    text: str
    voice_id: str


@dataclass
class PodcastBuildRequest:
    title: str
    segments: list[PodcastSegment]
    bgm_prompt: str | None = None
    export_format: str = "mp3"


@dataclass
class PodcastBuildResult:
    artifact_id: str
    final_audio_path: Path
    transcript_path: Path | None
    subtitle_srt_path: Path | None
    duration_sec: float


class PodcastFullProductionService:
    """Production contract for podcast generation.

    Real implementation must orchestrate TTS per segment, timeline placement,
    ducking, loudness normalization, final export, and artifact persistence.
    """

    async def build_episode(self, request: PodcastBuildRequest) -> PodcastBuildResult:
        raise NotImplementedError(
            "Podcast production requires TTS orchestration, timeline, ducking, normalize, export, and artifact persistence."
        )
