from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "audio_ai_workers",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.audio_tasks",
        "app.workers.clone_tasks",
        "app.workers.podcast_tasks",
    ],
)

celery_app.conf.update(
    task_default_queue="audio",
    task_routes={
        "audio.*": {"queue": "audio"},
        "podcast.*": {"queue": "audio"},
    },
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    beat_schedule={
        # Heartbeat: emits a no-op every 60 s so Flower shows the beat is alive
        "beat-heartbeat": {
            "task": "app.workers.celery_app._heartbeat",
            "schedule": 60.0,
        },
    },
)


@celery_app.task(name="app.workers.celery_app._heartbeat")
def _heartbeat() -> str:
    return "ok"
