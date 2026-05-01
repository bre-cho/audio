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
    bgm_prompt: str | None = None,
    export_format: str = "mp3",
) -> dict:
    """Full production task: TTS → mix → (optional) ducking → export.

    Each element of ``segments`` must have keys: ``speaker``, ``text``, ``voice_id``.
    """
    try:
        request = PodcastBuildRequest(
            title=title,
            segments=[PodcastSegment(**s) for s in segments],
            bgm_prompt=bgm_prompt,
            export_format=export_format,
        )
        service = PodcastFullProductionService()
        result = asyncio.get_event_loop().run_until_complete(service.build_episode(request))
        return {
            "status": "completed",
            "artifact_id": result.artifact_id,
            "final_audio_path": str(result.final_audio_path),
            "duration_sec": result.duration_sec,
        }
    except Exception as exc:
        raise self.retry(exc=exc)
