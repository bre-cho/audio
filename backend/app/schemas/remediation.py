from datetime import datetime

from pydantic import BaseModel, Field


class RemediationCreate(BaseModel):
    trigger_source: str = Field(pattern="^(regression|canary|incident|slo_breach)$")
    runbook_id: str
    action_plan: list[dict] = Field(default_factory=list)
    risk_level: str = Field(pattern="^(low|medium|high|critical)$")
    blast_radius_estimate: str = Field(pattern="^(low|medium|high|critical)$")
    confidence_score: int = Field(ge=0, le=100)
    auto_apply_allowed: bool = False


class RemediationOut(BaseModel):
    remediation_id: str
    trigger_source: str
    runbook_id: str
    risk_level: str
    blast_radius_estimate: str
    confidence_score: int
    approval_tier: str
    execution_allowed: bool
    execution_status: str
    verification_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RunbookCreate(BaseModel):
    title: str
    root_cause_hint: str
    owner: str
    verification_command: str
    steps: list[str] = Field(default_factory=list)


class RunbookOut(BaseModel):
    runbook_id: str
    title: str
    owner: str
    verification_command: str
    steps: list
    created_at: datetime

    model_config = {"from_attributes": True}


class RecoveryDrillRequest(BaseModel):
    policy_version: str
    simulate: bool = True


class RecoveryDrillOut(BaseModel):
    passed: bool
    policy_version: str
    rollback_target: str | None
    message: str