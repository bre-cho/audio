from datetime import datetime

from pydantic import BaseModel, Field


class BaselineCreate(BaseModel):
    artifact_id: str
    baseline_type: str = Field(pattern="^(golden|canary|regression)$")
    owner: str
    approved_by: str
    retention_days: int = Field(default=90, ge=1)
    replay_schedule: str = "nightly"
    drift_budget_policy: str


class BaselineTransition(BaseModel):
    lifecycle_state: str = Field(pattern="^(candidate|canary_active|active|deprecated|frozen|archived)$")


class CanaryEvaluationRequest(BaseModel):
    confidence_score: int = Field(ge=0, le=100)
    sample_size: int = Field(ge=1)
    min_required_samples: int = Field(default=30, ge=1)
    segment_coverage_ok: bool = True


class BaselineOut(BaseModel):
    baseline_id: str
    artifact_id: str
    baseline_type: str
    owner: str
    approved_by: str
    retention_days: int
    replay_schedule: str
    drift_budget_policy: str
    status: str
    lifecycle_state: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CanaryEvaluationOut(BaseModel):
    action: str
    freeze_candidate: bool
    rollback_required: bool
    reason: str


class SegmentRollbackRequest(BaseModel):
    segment_key: str
    critical: bool = False


class SegmentRollbackOut(BaseModel):
    action: str
    segment_key: str
    reason: str


class BlastRadiusRequest(BaseModel):
    affected_projects: int = Field(ge=0)
    affected_jobs: int = Field(ge=0)
    affected_artifacts: int = Field(ge=0)
    affected_users: int = Field(ge=0)
    affected_publish_queue: int = Field(ge=0)


class BlastRadiusOut(BaseModel):
    level: str
    score: int