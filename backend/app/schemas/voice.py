from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class VoiceListFilters(BaseModel):
    provider: str | None = None
    language_code: str | None = None
    source_type: str | None = None


class VoiceOut(BaseModel):
    id: UUID
    name: str
    source_type: str
    language_code: str | None = None
    gender: str | None = None
    preview_url: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {'from_attributes': True}


class VoiceUpdate(BaseModel):
    name: str | None = None
    visibility: str | None = None
    metadata_json: dict | None = None
