import uuid
from uuid import UUID
from sqlalchemy.orm import Session
from app.repositories.credit_repo import CreditRepository
from app.repositories.job_repo import JobRepository
from app.schemas.job import JobStatusOut
from app.schemas.voice_clone import VoiceCloneCreateRequest, VoiceClonePreviewRequest
from app.workers.clone_tasks import enqueue_clone_job, enqueue_clone_preview_job


class VoiceCloneService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.jobs = JobRepository(db)
        self.credits = CreditRepository(db)
        self.default_user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')

    def submit_clone(self, payload: VoiceCloneCreateRequest) -> JobStatusOut:
        if not payload.consent_confirmed:
            raise ValueError('consent_confirmed must be true')
        self.credits.add_event(user_id=self.default_user_id, delta_credits=-1000, event_type='reserve', note='voice clone reserve')
        job = self.jobs.create(user_id=self.default_user_id, job_type='clone', request_json=payload.model_dump(mode='json'))
        enqueue_clone_job(str(job.id))
        return JobStatusOut.model_validate(job)

    def submit_preview(self, voice_id: UUID, payload: VoiceClonePreviewRequest) -> JobStatusOut:
        job = self.jobs.create(user_id=self.default_user_id, job_type='clone_preview', request_json=payload.model_dump(mode='json'), voice_id=voice_id)
        enqueue_clone_preview_job(str(job.id))
        return JobStatusOut.model_validate(job)
