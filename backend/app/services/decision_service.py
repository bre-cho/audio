from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.decision import DecisionRecord
from app.schemas.decision import DecisionCreate, DecisionOutcomeUpdate


class DecisionService:
    def __init__(self, db: Session):
        self.db = db

    def create_decision(self, payload: DecisionCreate) -> DecisionRecord:
        decision = DecisionRecord(
            decision_id=str(uuid.uuid4()),
            trigger_type=payload.trigger_type,
            scenarios_considered=payload.scenarios_considered,
            selected_action=payload.selected_action,
            rejected_actions=payload.rejected_actions,
            score_breakdown=payload.score_breakdown,
            selected_reason=payload.selected_reason,
            confidence_score=payload.confidence_score,
            policy_version=payload.policy_version,
            decision_actor=payload.decision_actor,
            execution_status="pending",
            outcome_tracking_id=str(uuid.uuid4()),
        )
        self.db.add(decision)
        self.db.commit()
        self.db.refresh(decision)
        return decision

    def list_decisions(self) -> list[DecisionRecord]:
        return self.db.query(DecisionRecord).order_by(DecisionRecord.created_at.desc()).all()

    def get_by_decision_id(self, decision_id: str) -> DecisionRecord | None:
        return self.db.query(DecisionRecord).filter(DecisionRecord.decision_id == decision_id).one_or_none()

    def update_outcome(self, decision: DecisionRecord, payload: DecisionOutcomeUpdate) -> DecisionRecord:
        decision.execution_status = payload.execution_status
        decision.actual_json = payload.actual_json
        self.db.commit()
        self.db.refresh(decision)
        return decision

    def simulate_actions(self, *, scenarios: list[dict], candidate_actions: list[str]) -> dict:
        # Lightweight what-if scoring: lower risk and higher confidence win.
        avg_risk = 0
        avg_confidence = 0
        if scenarios:
            avg_risk = int(sum(int(s.get("risk", 50)) for s in scenarios) / len(scenarios))
            avg_confidence = int(sum(int(s.get("confidence", 50)) for s in scenarios) / len(scenarios))

        scores: dict[str, int] = {}
        for action in candidate_actions:
            action_bias = {
                "rollback": 5,
                "fallback": 10,
                "partial_freeze": 8,
                "delay": 2,
                "promote": -5,
            }.get(action, 0)
            score = max(0, min(100, (100 - avg_risk) + avg_confidence + action_bias))
            scores[action] = score

        selected_action = max(scores, key=scores.get)
        return {
            "selected_action": selected_action,
            "action_scores": scores,
        }