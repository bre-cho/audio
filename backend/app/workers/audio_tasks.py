from app.workers.celery_app import celery_app


def enqueue_tts_job(job_id: str) -> None:
    process_tts_job.delay(job_id)


def enqueue_conversation_job(job_id: str) -> None:
    process_conversation_job.delay(job_id)


def enqueue_batch_job(job_id: str) -> None:
    process_batch_job.delay(job_id)


@celery_app.task(name='audio.process_tts_job')
def process_tts_job(job_id: str) -> dict:
    return {'job_id': job_id, 'status': 'queued'}


@celery_app.task(name='audio.process_conversation_job')
def process_conversation_job(job_id: str) -> dict:
    return {'job_id': job_id, 'status': 'queued'}


@celery_app.task(name='audio.process_batch_job')
def process_batch_job(job_id: str) -> dict:
    return {'job_id': job_id, 'status': 'queued'}
