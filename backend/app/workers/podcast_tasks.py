from __future__ import annotations

import asyncio

from app.workers.celery_app import celery_app
from app.services.podcast_episode_builder import PodcastEpisodeBuilder
from app.services.podcast_full_production_service import (
    PodcastBuildRequest,
    PodcastFullProductionService,
    PodcastSegment,
)


@celery_app.task(name="podcast.build_episode_plan")
def build_episode_plan_task(title: str, script: str, speakers: list[str] | None = None) -> dict:
    return PodcastEpisodeBuilder().build_plan(title=title, script=script, speakers=speakers).dict()


@celery_app.task(
    name="podcast.produce_episode",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def produce_episode_task(
    self,
    title: str,
    segments: list[dict],
    bgm_file_path: str | None = None,
    export_format: str = "mp3",
) -> dict:
    """Full production task: TTS → mix → (optional) ducking → export.

    Each element of ``segments`` must have keys: ``speaker``, ``text``, ``voice_id``.
    ``bgm_file_path`` should be a path to a pre-generated BGM WAV file; use
    ``BGMGenerationService`` first if you need prompt-based BGM.
    """
    try:
        request = PodcastBuildRequest(
            title=title,
            segments=[PodcastSegment(**s) for s in segments],
            bgm_file_path=bgm_file_path,
            export_format=export_format,
        )
        service = PodcastFullProductionService()
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(service.build_episode(request))
        finally:
            loop.close()
        return {
            "status": "completed",
            "artifact_id": result.artifact_id,
            "final_audio_path": str(result.final_audio_path),
            "duration_sec": result.duration_sec,
        }
    except Exception as exc:
        raise self.retry(exc=exc)
