from celery import Celery
from app.core.config import settings

celery_app = Celery('audio_ai_workers', broker=settings.redis_url, backend=settings.redis_url)
