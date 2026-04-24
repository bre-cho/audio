import uuid
from sqlalchemy.orm import Session
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
