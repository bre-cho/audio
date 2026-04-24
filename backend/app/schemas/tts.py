from uuid import UUID
from pydantic import BaseModel, Field


class TTSGenerateRequest(BaseModel):
    text: str = Field(min_length=1)
    provider: str | None = None
    model: str | None = None
    voice_id: UUID | None = None
    format: str = 'mp3'
    speed: float = 1.0
    stability: float | None = None
    similarity_boost: float | None = None
    style: float | None = None
    speaker_boost: bool = True
    project_id: UUID | None = None


class TTSPreviewRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    provider: str | None = None
    model: str | None = None
    voice_id: UUID | None = None
