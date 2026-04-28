from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, computed_field


class JobStatusOut(BaseModel):
    id: UUID
    job_type: str
    idempotency_key: str | None = None
    status: Literal["queued", "processing", "retrying", "succeeded", "success", "done", "failed"]
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
        """Alias for `id` — exposed as `job_id` to match client and worker conventions."""
        return self.id
