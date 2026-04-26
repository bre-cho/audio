from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.remediation import RecoveryDrillOut, RecoveryDrillRequest, RunbookCreate, RunbookOut
from app.services.recovery_service import RecoveryService

router = APIRouter()


@router.get("/runbooks", response_model=list[RunbookOut])
def list_runbooks(db: Session = Depends(get_db)) -> list[RunbookOut]:
    return RecoveryService(db).list_runbooks()


@router.post("/runbooks", response_model=RunbookOut)
def create_runbook(payload: RunbookCreate, db: Session = Depends(get_db)) -> RunbookOut:
    return RecoveryService(db).create_runbook(payload)


@router.post("/drill", response_model=RecoveryDrillOut)
def run_recovery_drill(payload: RecoveryDrillRequest, db: Session = Depends(get_db)) -> RecoveryDrillOut:
    result = RecoveryService(db).run_recovery_drill(payload)
    return RecoveryDrillOut(**result)


@router.post("/runbooks/{runbook_id}/execute")
def execute_runbook(runbook_id: str, db: Session = Depends(get_db)) -> dict:
    try:
        return RecoveryService(db).execute_runbook(runbook_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/last-safe-policy/{policy_version}")
def register_last_safe_policy(policy_version: str, db: Session = Depends(get_db)) -> dict:
    row = RecoveryService(db).register_last_safe_policy(policy_version=policy_version)
    return {"policy_version": row.policy_version, "recorded_by": row.recorded_by}