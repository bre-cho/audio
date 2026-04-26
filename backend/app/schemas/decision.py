from datetime import datetime

from pydantic import BaseModel, Field


class DecisionCreate(BaseModel):
    trigger_type: str
    scenarios_considered: list[dict] = Field(min_length=1)
    selected_action: str
    rejected_actions: list[str] = Field(default_factory=list)
    score_breakdown: dict
    selected_reason: str
    confidence_score: int = Field(ge=0, le=100)
    policy_version: str
    decision_actor: str = Field(pattern="^(system|ci|operator)$")


class DecisionOutcomeUpdate(BaseModel):
    execution_status: str = Field(pattern="^(pending|executed|failed)$")
    actual_json: dict = Field(default_factory=dict)


class DecisionOut(BaseModel):
    decision_id: str
    trigger_type: str
    selected_action: str
    confidence_score: int
    policy_version: str
    decision_actor: str
    execution_status: str
    outcome_tracking_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DecisionSimulationRequest(BaseModel):
    scenarios: list[dict] = Field(min_length=1)
    candidate_actions: list[str] = Field(min_length=1)


class DecisionSimulationOut(BaseModel):
    selected_action: str
    action_scores: dict[str, int]