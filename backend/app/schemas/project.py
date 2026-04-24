from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    project_type: str = 'audio'
    status: str = 'draft'
    settings_json: dict = {}


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    settings_json: dict | None = None


class ProjectOut(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    project_type: str
    status: str
    settings_json: dict
    created_at: datetime

    model_config = {'from_attributes': True}


class ProjectScriptCreate(BaseModel):
    asset_type: str
    title: str | None = None
    raw_text: str
    language_code: str | None = None
    metadata_json: dict = {}
