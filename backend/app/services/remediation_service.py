from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.remediation import RemediationRecord
from app.schemas.remediation import RemediationCreate


class RemediationService:
    def __init__(self, db: Session):
        self.db = db

    def compute_approval_tier(self, *, risk_level: str, blast_radius_estimate: str, confidence_score: int) -> str:
        if risk_level == "critical":
            return "tier_3"
        if risk_level == "high" or blast_radius_estimate in {"high", "critical"}:
            return "tier_2"
        if risk_level == "medium" and confidence_score >= 85:
            return "tier_1"
        if risk_level == "low" and blast_radius_estimate == "low" and confidence_score >= 90:
            return "tier_0"
        return "tier_2"

    def is_execution_allowed(self, *, approval_tier: str, auto_apply_allowed: bool) -> bool:
        if approval_tier == "tier_0":
            return auto_apply_allowed
        if approval_tier == "tier_1":
            return auto_apply_allowed
        return False

    def create_remediation(self, payload: RemediationCreate) -> RemediationRecord:
        tier = self.compute_approval_tier(
            risk_level=payload.risk_level,
            blast_radius_estimate=payload.blast_radius_estimate,
            confidence_score=payload.confidence_score,
        )
        execution_allowed = self.is_execution_allowed(approval_tier=tier, auto_apply_allowed=payload.auto_apply_allowed)
        remediation = RemediationRecord(
            remediation_id=str(uuid.uuid4()),
            trigger_source=payload.trigger_source,
            runbook_id=payload.runbook_id,
            action_plan=payload.action_plan,
            auto_apply_allowed=payload.auto_apply_allowed,
            risk_level=payload.risk_level,
            blast_radius_estimate=payload.blast_radius_estimate,
            confidence_score=payload.confidence_score,
            execution_status="pending",
            verification_status="pending",
            human_override_required=tier in {"tier_2", "tier_3"},
            approval_tier=tier,
            execution_allowed=execution_allowed,
        )
        self.db.add(remediation)
        self.db.commit()
        self.db.refresh(remediation)
        return remediation

    def list_remediations(self) -> list[RemediationRecord]:
        return self.db.query(RemediationRecord).order_by(RemediationRecord.created_at.desc()).all()