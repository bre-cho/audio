from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.audio_factory.task_mapper import build_conversation_task
from app.schemas.conversation import ConversationGenerateRequest, ConversationParseRequest, ConversationParseResponse
from app.schemas.job import JobStatusOut
from app.services.conversation_service import ConversationService

router = APIRouter()


@router.post('/parse', response_model=ConversationParseResponse)
def parse_conversation(payload: ConversationParseRequest) -> ConversationParseResponse:
    return ConversationService.parse(payload)


@router.post('/generate', response_model=JobStatusOut)
def generate_conversation(
    payload: ConversationGenerateRequest,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias='Idempotency-Key'),
) -> JobStatusOut:
    task = build_conversation_task(payload)
    return ConversationService(db).submit_generate_task(task, payload.project_id, idempotency_key=idempotency_key)
