from uuid import UUID
from pydantic import BaseModel, Field


class ConversationLine(BaseModel):
    speaker: str
    text: str


class ConversationParseRequest(BaseModel):
    raw_script: str = Field(min_length=1)


class ConversationParseResponse(BaseModel):
    lines: list[ConversationLine]


class ConversationGenerateRequest(BaseModel):
    script: list[ConversationLine]
    speaker_voice_map: dict[str, UUID | None]
    provider_strategy: str = 'per_voice'
    merge_output: bool = True
    project_id: UUID | None = None
