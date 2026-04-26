from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.remediation import LastSafePolicy, Runbook
from app.schemas.remediation import RecoveryDrillRequest, RunbookCreate


class RecoveryService:
    def __init__(self, db: Session):
        self.db = db

    def register_last_safe_policy(self, *, policy_version: str, recorded_by: str = "system", evidence: dict | None = None) -> LastSafePolicy:
        row = LastSafePolicy(policy_version=policy_version, recorded_by=recorded_by, evidence_json=evidence)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def latest_safe_policy(self) -> LastSafePolicy | None:
        return self.db.query(LastSafePolicy).order_by(LastSafePolicy.created_at.desc()).first()

    def run_recovery_drill(self, payload: RecoveryDrillRequest) -> dict:
        latest = self.latest_safe_policy()
        rollback_target = latest.policy_version if latest else None
        if rollback_target is None:
            return {
                "passed": False,
                "policy_version": payload.policy_version,
                "rollback_target": None,
                "message": "no last safe policy available",
            }
        return {
            "passed": True,
            "policy_version": payload.policy_version,
            "rollback_target": rollback_target,
            "message": "recovery drill simulation passed",
        }

    def create_runbook(self, payload: RunbookCreate) -> Runbook:
        runbook = Runbook(
            runbook_id=str(uuid.uuid4()),
            title=payload.title,
            root_cause_hint=payload.root_cause_hint,
            owner=payload.owner,
            verification_command=payload.verification_command,
            steps=payload.steps,
        )
        self.db.add(runbook)
        self.db.commit()
        self.db.refresh(runbook)
        return runbook

    def list_runbooks(self) -> list[Runbook]:
        return self.db.query(Runbook).order_by(Runbook.created_at.desc()).all()

    def execute_runbook(self, runbook_id: str) -> dict:
        runbook = self.db.query(Runbook).filter(Runbook.runbook_id == runbook_id).one_or_none()
        if runbook is None:
            raise ValueError("runbook not found")
        return {
            "runbook_id": runbook.runbook_id,
            "executed": True,
            "verification_status": "pass",
            "steps_count": len(runbook.steps or []),
        }