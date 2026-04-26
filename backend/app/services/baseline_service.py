from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.baseline import Baseline
from app.schemas.baseline import BaselineCreate, CanaryEvaluationRequest


class BaselineService:
    VALID_TRANSITIONS = {
        "candidate": {"canary_active", "frozen", "archived"},
        "canary_active": {"active", "frozen", "archived"},
        "active": {"deprecated", "frozen"},
        "deprecated": {"archived", "frozen"},
        "frozen": {"archived"},
        "archived": set(),
    }

    def __init__(self, db: Session):
        self.db = db

    def create_baseline(self, payload: BaselineCreate) -> Baseline:
        baseline = Baseline(
            baseline_id=str(uuid.uuid4()),
            artifact_id=payload.artifact_id,
            baseline_type=payload.baseline_type,
            owner=payload.owner,
            approved_by=payload.approved_by,
            retention_days=payload.retention_days,
            replay_schedule=payload.replay_schedule,
            drift_budget_policy=payload.drift_budget_policy,
            status="standby",
            lifecycle_state="candidate",
        )
        self.db.add(baseline)
        self.db.commit()
        self.db.refresh(baseline)
        return baseline

    def list_baselines(self) -> list[Baseline]:
        return self.db.query(Baseline).order_by(Baseline.created_at.desc()).all()

    def get_by_baseline_id(self, baseline_id: str) -> Baseline | None:
        return self.db.query(Baseline).filter(Baseline.baseline_id == baseline_id).one_or_none()

    def get_active(self, baseline_type: str) -> Baseline | None:
        return (
            self.db.query(Baseline)
            .filter(Baseline.baseline_type == baseline_type, Baseline.lifecycle_state == "active", Baseline.status == "active")
            .order_by(Baseline.updated_at.desc())
            .first()
        )

    def transition(self, baseline: Baseline, to_state: str) -> Baseline:
        if to_state not in self.VALID_TRANSITIONS.get(baseline.lifecycle_state, set()):
            raise ValueError(f"invalid lifecycle transition: {baseline.lifecycle_state} -> {to_state}")

        baseline.lifecycle_state = to_state
        if to_state == "active":
            baseline.status = "active"
        elif to_state in {"deprecated", "frozen"}:
            baseline.status = to_state
        elif to_state == "archived":
            baseline.status = "deprecated"
        else:
            baseline.status = "standby"

        self.db.commit()
        self.db.refresh(baseline)
        return baseline

    def evaluate_canary(self, payload: CanaryEvaluationRequest) -> dict:
        if payload.sample_size < payload.min_required_samples:
            return {
                "action": "extend",
                "freeze_candidate": False,
                "rollback_required": False,
                "reason": "insufficient sample size for confidence scoring",
            }

        if not payload.segment_coverage_ok:
            return {
                "action": "extend",
                "freeze_candidate": False,
                "rollback_required": False,
                "reason": "segment coverage incomplete",
            }

        if payload.confidence_score >= 90:
            return {
                "action": "promote",
                "freeze_candidate": False,
                "rollback_required": False,
                "reason": "confidence score >= 90",
            }
        if payload.confidence_score >= 70:
            return {
                "action": "extend",
                "freeze_candidate": False,
                "rollback_required": False,
                "reason": "confidence score in 70-89 range",
            }
        return {
            "action": "rollback",
            "freeze_candidate": True,
            "rollback_required": True,
            "reason": "confidence score < 70",
        }

    def segment_rollback_action(self, *, segment_key: str, critical: bool) -> dict:
        if critical:
            return {
                "action": "full_rollback",
                "segment_key": segment_key,
                "reason": "critical segment failure",
            }
        return {
            "action": "segment_freeze_and_fallback",
            "segment_key": segment_key,
            "reason": "non-critical segment issue isolated",
        }

    def estimate_blast_radius(
        self,
        *,
        affected_projects: int,
        affected_jobs: int,
        affected_artifacts: int,
        affected_users: int,
        affected_publish_queue: int,
    ) -> dict:
        score = (
            affected_projects
            + affected_jobs
            + affected_artifacts
            + (affected_users * 2)
            + affected_publish_queue
        )
        if score >= 500:
            level = "critical"
        elif score >= 200:
            level = "high"
        elif score >= 80:
            level = "medium"
        else:
            level = "low"
        return {"level": level, "score": score}