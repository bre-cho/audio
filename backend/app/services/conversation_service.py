import uuid
from sqlalchemy.orm import Session
from app.audio_factory.schemas import AudioTaskRequest
from app.repositories.job_repo import JobRepository
from app.schemas.conversation import ConversationGenerateRequest, ConversationParseRequest, ConversationParseResponse, ConversationLine
from app.schemas.job import JobStatusOut
from app.workers.audio_tasks import enqueue_conversation_job


class ConversationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.jobs = JobRepository(db)
        self.default_user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')

    @staticmethod
    def parse(payload: ConversationParseRequest) -> ConversationParseResponse:
        lines: list[ConversationLine] = []
        for raw in payload.raw_script.splitlines():
            raw = raw.strip()
            if not raw or ':' not in raw:
                continue
            speaker, text = raw.split(':', 1)
            lines.append(ConversationLine(speaker=speaker.strip(), text=text.strip()))
        return ConversationParseResponse(lines=lines)

    def submit_generate(self, payload: ConversationGenerateRequest) -> JobStatusOut:
        job = self.jobs.create(user_id=self.default_user_id, job_type='conversation', request_json=payload.model_dump(mode='json'), project_id=payload.project_id)
        enqueue_conversation_job(str(job.id))
        return JobStatusOut.model_validate(job)

    def submit_generate_task(
        self,
        task: AudioTaskRequest,
        project_id,
        idempotency_key: str | None = None,
    ) -> JobStatusOut:
        job, created = self.jobs.create_or_get(
            user_id=self.default_user_id,
            job_type='conversation',
            workflow_type=task.workflow_type.value,
            request_json=task.request_json,
            project_id=project_id,
            idempotency_key=idempotency_key,
        )
        if created:
            enqueue_conversation_job(str(job.id))
        return JobStatusOut.model_validate(job)
