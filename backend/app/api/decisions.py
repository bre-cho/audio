from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.decision import (
    DecisionCreate,
    DecisionOutcomeUpdate,
    DecisionOut,
    DecisionSimulationOut,
    DecisionSimulationRequest,
)
from app.services.decision_service import DecisionService

router = APIRouter()


@router.get("", response_model=list[DecisionOut])
def list_decisions(db: Session = Depends(get_db)) -> list[DecisionOut]:
    return DecisionService(db).list_decisions()


@router.post("", response_model=DecisionOut)
def create_decision(payload: DecisionCreate, db: Session = Depends(get_db)) -> DecisionOut:
    return DecisionService(db).create_decision(payload)


@router.patch("/{decision_id}", response_model=DecisionOut)
def update_decision_outcome(
    decision_id: str,
    payload: DecisionOutcomeUpdate,
    db: Session = Depends(get_db),
) -> DecisionOut:
    service = DecisionService(db)
    decision = service.get_by_decision_id(decision_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="Khong tim thay decision")
    return service.update_outcome(decision, payload)


@router.post("/simulate", response_model=DecisionSimulationOut)
def simulate_decisions(payload: DecisionSimulationRequest, db: Session = Depends(get_db)) -> DecisionSimulationOut:
    result = DecisionService(db).simulate_actions(
        scenarios=payload.scenarios,
        candidate_actions=payload.candidate_actions,
    )
    return DecisionSimulationOut(**result)