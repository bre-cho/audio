import uuid
from uuid import UUID
from sqlalchemy.orm import Session
from app.audio_factory.schemas import AudioTaskRequest
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

    def submit_clone(self, payload: VoiceCloneCreateRequest, idempotency_key: str | None = None) -> JobStatusOut:
        if not payload.consent_confirmed:
            raise ValueError('consent_confirmed must be true')
        job, created = self.jobs.create_or_get(
            user_id=self.default_user_id,
            job_type='clone',
            request_json=payload.model_dump(mode='json'),
            idempotency_key=idempotency_key,
        )
        if created:
            self.credits.add_event(
                user_id=self.default_user_id,
                delta_credits=-1000,
                event_type='reserve',
                note='voice clone reserve',
            )
            enqueue_clone_job(str(job.id))
        return JobStatusOut.model_validate(job)

    def submit_preview(self, voice_id: UUID, payload: VoiceClonePreviewRequest) -> JobStatusOut:
        job = self.jobs.create(user_id=self.default_user_id, job_type='clone_preview', request_json=payload.model_dump(mode='json'), voice_id=voice_id)
        enqueue_clone_preview_job(str(job.id))
        return JobStatusOut.model_validate(job)

    def submit_preview_task(
        self,
        voice_id: UUID,
        task: AudioTaskRequest,
        idempotency_key: str | None = None,
    ) -> JobStatusOut:
        job, created = self.jobs.create_or_get(
            user_id=self.default_user_id,
            job_type='clone_preview',
            workflow_type=task.workflow_type.value,
            request_json=task.request_json,
            voice_id=voice_id,
            idempotency_key=idempotency_key,
        )
        if created:
            enqueue_clone_preview_job(str(job.id))
        return JobStatusOut.model_validate(job)
