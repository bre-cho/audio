from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "audio_ai_workers",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.audio_tasks",
        "app.workers.clone_tasks",
    ],
)

celery_app.conf.update(
    task_default_queue="audio",
    task_routes={
        "audio.*": {"queue": "audio"},
    },
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)
