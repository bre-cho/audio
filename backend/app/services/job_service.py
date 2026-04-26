from uuid import UUID
from sqlalchemy.orm import Session
from app.repositories.job_repo import JobRepository
from app.schemas.job import JobStatusOut
from app.workers.audio_tasks import enqueue_tts_job, enqueue_batch_job
from app.workers.clone_tasks import enqueue_clone_job, enqueue_clone_preview_job

RETRYABLE_JOB_TYPES = {
    "tts",
    "tts_preview",
    "narration",
    "conversation",
    "clone",
    "clone_preview",
}


class UnsupportedRetryJobTypeError(Exception):
    pass


class JobService:
    def __init__(self, db: Session) -> None:
        self.repo = JobRepository(db)

    def list_jobs(self) -> list[JobStatusOut]:
        return [JobStatusOut.model_validate(job) for job in self.repo.list()]

    def get_job(self, job_id: UUID) -> JobStatusOut | None:
        job = self.repo.get(job_id)
        return JobStatusOut.model_validate(job) if job else None

    def retry_job(self, job_id: UUID) -> JobStatusOut:
        job = self.repo.get(job_id)
        if not job:
            raise ValueError('Job not found')

        if job.job_type not in RETRYABLE_JOB_TYPES:
            raise UnsupportedRetryJobTypeError(f"Unsupported job type for retry: {job.job_type}")

        job.status = 'queued'
        job.error_code = None
        job.error_message = None
        self.repo.db.add(job)
        self.repo.db.commit()
        self.repo.db.refresh(job)

        workflow_type = job.workflow_type or job.job_type

        if workflow_type in {'tts_generate', 'tts_preview'} or job.job_type in {'tts', 'tts_preview'}:
            enqueue_tts_job(str(job.id))
        elif workflow_type == 'narration' or job.job_type == 'narration':
            enqueue_batch_job(str(job.id))
        elif workflow_type == 'conversation' or job.job_type == 'conversation':
            from app.workers.audio_tasks import enqueue_conversation_job

            enqueue_conversation_job(str(job.id))
        elif workflow_type == 'clone_preview' or job.job_type == 'clone_preview':
            enqueue_clone_preview_job(str(job.id))
        elif job.job_type == 'clone':
            enqueue_clone_job(str(job.id))

        return JobStatusOut.model_validate(job)
