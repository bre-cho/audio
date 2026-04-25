import uuid
from sqlalchemy.orm import Session
from app.audio_factory.schemas import AudioTaskRequest
from app.core.credits import CreditPolicy
from app.repositories.credit_repo import CreditRepository
from app.repositories.job_repo import JobRepository
from app.schemas.job import JobStatusOut
from app.schemas.tts import TTSGenerateRequest, TTSPreviewRequest
from app.services.provider_router import ProviderRouter
from app.workers.audio_tasks import enqueue_tts_job


class TTSService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.jobs = JobRepository(db)
        self.credits = CreditRepository(db)
        self.router = ProviderRouter()
        self.default_user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')

    def submit_generate(self, payload: TTSGenerateRequest) -> JobStatusOut:
        estimate = CreditPolicy.estimate_tts(len(payload.text))
        self.credits.add_event(user_id=self.default_user_id, delta_credits=-estimate.estimated_credits, event_type='reserve', note='tts generate reserve')
        job = self.jobs.create(user_id=self.default_user_id, job_type='tts', request_json=payload.model_dump(mode='json'), project_id=payload.project_id, voice_id=payload.voice_id)
        enqueue_tts_job(str(job.id))
        return JobStatusOut.model_validate(job)

    def submit_preview(self, payload: TTSPreviewRequest) -> JobStatusOut:
        job = self.jobs.create(user_id=self.default_user_id, job_type='tts_preview', request_json=payload.model_dump(mode='json'), voice_id=payload.voice_id)
        enqueue_tts_job(str(job.id))
        return JobStatusOut.model_validate(job)

    def submit_generate_task(
        self,
        task: AudioTaskRequest,
        payload: TTSGenerateRequest,
        idempotency_key: str | None = None,
    ) -> JobStatusOut:
        estimate = CreditPolicy.estimate_tts(len(task.text or ""))
        job, created = self.jobs.create_or_get(
            user_id=self.default_user_id,
            job_type='tts',
            workflow_type=task.workflow_type.value,
            request_json=task.request_json,
            project_id=payload.project_id,
            voice_id=payload.voice_id,
            idempotency_key=idempotency_key,
        )
        if created:
            self.credits.add_event(
                user_id=self.default_user_id,
                delta_credits=-estimate.estimated_credits,
                event_type='reserve',
                note='tts generate reserve',
            )
            enqueue_tts_job(str(job.id))
        return JobStatusOut.model_validate(job)

    def submit_preview_task(
        self,
        task: AudioTaskRequest,
        payload: TTSPreviewRequest,
        idempotency_key: str | None = None,
    ) -> JobStatusOut:
        job, created = self.jobs.create_or_get(
            user_id=self.default_user_id,
            job_type='tts_preview',
            workflow_type=task.workflow_type.value,
            request_json=task.request_json,
            voice_id=payload.voice_id,
            idempotency_key=idempotency_key,
        )
        if created:
            enqueue_tts_job(str(job.id))
        return JobStatusOut.model_validate(job)
