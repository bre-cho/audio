from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class JobStatusOut(BaseModel):
    id: UUID
    job_type: str
    status: str
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}
