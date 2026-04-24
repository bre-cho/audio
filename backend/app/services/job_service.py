from uuid import UUID
from sqlalchemy.orm import Session
from app.repositories.job_repo import JobRepository
from app.schemas.job import JobStatusOut


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
        job.status = 'queued'
        self.repo.db.add(job)
        self.repo.db.commit()
        self.repo.db.refresh(job)
        return JobStatusOut.model_validate(job)
