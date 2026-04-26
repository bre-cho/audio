from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.baseline import (
    BaselineCreate,
    BaselineOut,
    BaselineTransition,
    BlastRadiusOut,
    BlastRadiusRequest,
    CanaryEvaluationOut,
    CanaryEvaluationRequest,
    SegmentRollbackOut,
    SegmentRollbackRequest,
)
from app.services.baseline_service import BaselineService

router = APIRouter()


@router.get("", response_model=list[BaselineOut])
def list_baselines(db: Session = Depends(get_db)) -> list[BaselineOut]:
    return BaselineService(db).list_baselines()


@router.post("", response_model=BaselineOut)
def create_baseline(payload: BaselineCreate, db: Session = Depends(get_db)) -> BaselineOut:
    return BaselineService(db).create_baseline(payload)


@router.get("/active/{baseline_type}", response_model=BaselineOut)
def get_active_baseline(baseline_type: str, db: Session = Depends(get_db)) -> BaselineOut:
    baseline = BaselineService(db).get_active(baseline_type)
    if baseline is None:
        raise HTTPException(status_code=404, detail="Khong tim thay baseline active")
    return baseline


@router.post("/{baseline_id}/transition", response_model=BaselineOut)
def transition_baseline(
    baseline_id: str,
    payload: BaselineTransition,
    db: Session = Depends(get_db),
) -> BaselineOut:
    service = BaselineService(db)
    baseline = service.get_by_baseline_id(baseline_id)
    if baseline is None:
        raise HTTPException(status_code=404, detail="Khong tim thay baseline")
    try:
        return service.transition(baseline, payload.lifecycle_state)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/canary/evaluate", response_model=CanaryEvaluationOut)
def evaluate_canary(payload: CanaryEvaluationRequest, db: Session = Depends(get_db)) -> CanaryEvaluationOut:
    return CanaryEvaluationOut(**BaselineService(db).evaluate_canary(payload))


@router.post("/segment-rollback", response_model=SegmentRollbackOut)
def segment_rollback(payload: SegmentRollbackRequest, db: Session = Depends(get_db)) -> SegmentRollbackOut:
    result = BaselineService(db).segment_rollback_action(segment_key=payload.segment_key, critical=payload.critical)
    return SegmentRollbackOut(**result)


@router.post("/blast-radius", response_model=BlastRadiusOut)
def blast_radius(payload: BlastRadiusRequest, db: Session = Depends(get_db)) -> BlastRadiusOut:
    result = BaselineService(db).estimate_blast_radius(
        affected_projects=payload.affected_projects,
        affected_jobs=payload.affected_jobs,
        affected_artifacts=payload.affected_artifacts,
        affected_users=payload.affected_users,
        affected_publish_queue=payload.affected_publish_queue,
    )
    return BlastRadiusOut(**result)