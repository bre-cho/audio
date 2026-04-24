from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, computed_field


class JobStatusOut(BaseModel):
    id: UUID
    job_type: str
    status: str
    error_code: str | None = None
    error_message: str | None = None
    runtime_json: dict = Field(default_factory=dict)
    preview_url: str | None = None
    output_url: str | None = None
    voice_profile_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}

    @computed_field
    @property
    def job_id(self) -> UUID:
        return self.id
