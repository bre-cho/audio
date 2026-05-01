from __future__ import annotations

from app.workers.celery_app import celery_app
from app.services.podcast_episode_builder import PodcastEpisodeBuilder


@celery_app.task(name="podcast.build_episode_plan")
def build_episode_plan_task(title: str, script: str, speakers: list[str] | None = None) -> dict:
    return PodcastEpisodeBuilder().build_plan(title=title, script=script, speakers=speakers).dict()
