from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.remediation import RemediationCreate, RemediationOut
from app.services.remediation_service import RemediationService

router = APIRouter()


@router.get("", response_model=list[RemediationOut])
def list_remediations(db: Session = Depends(get_db)) -> list[RemediationOut]:
    return RemediationService(db).list_remediations()


@router.post("", response_model=RemediationOut)
def create_remediation(payload: RemediationCreate, db: Session = Depends(get_db)) -> RemediationOut:
    return RemediationService(db).create_remediation(payload)