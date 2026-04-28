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

    def submit_clone(
        self,
        payload: VoiceCloneCreateRequest,
        user_id: UUID | None = None,
        idempotency_key: str | None = None,
    ) -> JobStatusOut:
        current_user_id = user_id or uuid.UUID('00000000-0000-0000-0000-000000000001')
        if not payload.consent_confirmed:
            raise ValueError('consent_confirmed phai la true')
        job, created = self.jobs.create_or_get(
            user_id=current_user_id,
            job_type='clone',
            request_json=payload.model_dump(mode='json'),
            idempotency_key=idempotency_key,
        )
        if created:
            self.credits.add_event(
                user_id=current_user_id,
                delta_credits=-1000,
                event_type='reserve',
                note='giu cho clone giong noi',
            )
            enqueue_clone_job(str(job.id))
        return JobStatusOut.model_validate(job)

    def submit_preview(self, voice_id: UUID, payload: VoiceClonePreviewRequest, user_id: UUID | None = None) -> JobStatusOut:
        current_user_id = user_id or uuid.UUID('00000000-0000-0000-0000-000000000001')
        job = self.jobs.create(user_id=current_user_id, job_type='clone_preview', request_json=payload.model_dump(mode='json'), voice_id=voice_id)
        enqueue_clone_preview_job(str(job.id))
        return JobStatusOut.model_validate(job)

    def submit_preview_task(
        self,
        voice_id: UUID,
        task: AudioTaskRequest,
        user_id: UUID | None = None,
        idempotency_key: str | None = None,
    ) -> JobStatusOut:
        current_user_id = user_id or uuid.UUID('00000000-0000-0000-0000-000000000001')
        job, created = self.jobs.create_or_get(
            user_id=current_user_id,
            job_type='clone_preview',
            workflow_type=task.workflow_type.value,
            request_json=task.request_json,
            voice_id=voice_id,
            idempotency_key=idempotency_key,
        )
        if created:
            enqueue_clone_preview_job(str(job.id))
        return JobStatusOut.model_validate(job)

    def submit_shift_job(
        self,
        sample_file_id: str,
        user_id: UUID | None = None,
        pitch_semitones: float = 0,
        idempotency_key: str | None = None,
    ) -> JobStatusOut:
        current_user_id = user_id or uuid.UUID('00000000-0000-0000-0000-000000000001')
        job, created = self.jobs.create_or_get(
            user_id=current_user_id,
            job_type='voice_shift',
            request_json={'sample_file_id': sample_file_id, 'pitch_semitones': pitch_semitones},
            idempotency_key=idempotency_key,
        )
        if created:
            self.credits.add_event(
                user_id=current_user_id,
                delta_credits=-500,
                event_type='reserve',
                note='giu cho shift voice',
            )
        return JobStatusOut.model_validate(job)
