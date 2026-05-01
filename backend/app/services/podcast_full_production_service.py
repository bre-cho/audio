from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from app.services.podcast_ducking_service import PodcastDuckingService
from app.services.podcast_episode_builder import PodcastEpisodeBuilder
from app.services.podcast_export_service import PodcastExportService
from app.services.podcast_mixdown_service import PodcastMixdownService
from app.services.podcast_tts_orchestrator import PodcastTTSOrchestrator


@dataclass
class PodcastSegment:
    speaker: str
    text: str
    voice_id: str


@dataclass
class PodcastBuildRequest:
    title: str
    segments: list[PodcastSegment]
    bgm_file_path: str | None = None
    """Optional path to a pre-generated BGM WAV file for ducking.

    When set, the mixed voice track will be ducked under this BGM using
    :class:`PodcastDuckingService`.  Pass ``None`` to skip BGM altogether.
    Use ``BGMGenerationService`` first if you need to generate BGM from a prompt.
    """
    export_format: str = "mp3"


@dataclass
class PodcastBuildResult:
    artifact_id: str
    final_audio_path: Path
    transcript_path: Path | None
    subtitle_srt_path: Path | None
    duration_sec: float


class PodcastFullProductionService:
    """Orchestrate a full podcast production run.

    Flow:
      1. Build an episode plan from explicit segments.
      2. Synthesise TTS audio for every segment.
      3. Mix all segments into a single WAV (with optional BGM ducking).
      4. Validate the export.
    """

    def __init__(self, artifacts_root: str = "artifacts/podcast"):
        self._root = Path(artifacts_root)

    async def build_episode(self, request: PodcastBuildRequest) -> PodcastBuildResult:
        artifact_id = uuid.uuid4().hex
        work_dir = self._root / artifact_id
        work_dir.mkdir(parents=True, exist_ok=True)

        # 1. Build an episode plan dict from the provided segments
        script_lines = "\n".join(f"{s.speaker}: {s.text}" for s in request.segments)
        builder = PodcastEpisodeBuilder()
        plan = builder.build_plan(
            title=request.title,
            script=script_lines,
            speakers=list({s.speaker for s in request.segments}),
        )
        speaker_voice_map = {s.speaker: s.voice_id for s in request.segments}

        # 2. Synthesise TTS for every segment
        orchestrator = PodcastTTSOrchestrator(output_dir=str(work_dir / "segments"))
        synthesised = orchestrator.synthesize_segments(plan.dict(), speaker_voice_map)

        # 3. Mix all segments
        mixed_wav = str(work_dir / "mixed.wav")
        mixdown = PodcastMixdownService()
        mix_result = mixdown.render(synthesised, mixed_wav)

        final_audio_path = Path(mix_result["output_path"])

        # 4. Optional BGM ducking (only if a BGM track file path is provided)
        if request.bgm_file_path and Path(request.bgm_file_path).exists():
            ducked_wav = str(work_dir / "ducked.wav")
            ducking = PodcastDuckingService()
            ducked_path = ducking.apply_ducking(
                voice_track_path=str(final_audio_path),
                bgm_path=request.bgm_file_path,
                output_path=ducked_wav,
            )
            final_audio_path = Path(ducked_path)

        # 5. Validate export
        export_service = PodcastExportService()
        export_service.validate_export(str(final_audio_path))

        duration = mix_result.get("duration_sec", 0.0)

        return PodcastBuildResult(
            artifact_id=artifact_id,
            final_audio_path=final_audio_path,
            transcript_path=None,
            subtitle_srt_path=None,
            duration_sec=duration,
        )
