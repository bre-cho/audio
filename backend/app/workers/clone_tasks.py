from app.workers.celery_app import celery_app


def enqueue_clone_job(job_id: str) -> None:
    process_clone_job.delay(job_id)


def enqueue_clone_preview_job(job_id: str) -> None:
    process_clone_preview_job.delay(job_id)


@celery_app.task(name='audio.process_clone_job')
def process_clone_job(job_id: str) -> dict:
    return {'job_id': job_id, 'status': 'queued'}


@celery_app.task(name='audio.process_clone_preview_job')
def process_clone_preview_job(job_id: str) -> dict:
    return {'job_id': job_id, 'status': 'queued'}
