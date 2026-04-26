from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.job import JobStatusOut
from app.schemas.project import ProjectCreate, ProjectOut, ProjectScriptCreate, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter()


@router.post('', response_model=ProjectOut)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectOut:
    return ProjectService(db).create_project(payload)


@router.get('', response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)) -> list[ProjectOut]:
    return ProjectService(db).list_projects()


@router.get('/{project_id}', response_model=ProjectOut)
def get_project(project_id: UUID, db: Session = Depends(get_db)) -> ProjectOut:
    project = ProjectService(db).get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail='Khong tim thay du an')
    return project


@router.patch('/{project_id}', response_model=ProjectOut)
def update_project(project_id: UUID, payload: ProjectUpdate, db: Session = Depends(get_db)) -> ProjectOut:
    project = ProjectService(db).update_project(project_id, payload)
    if not project:
        raise HTTPException(status_code=404, detail='Khong tim thay du an')
    return project


@router.post('/{project_id}/scripts')
def add_script(project_id: UUID, payload: ProjectScriptCreate, db: Session = Depends(get_db)) -> dict:
    return ProjectService(db).add_script(project_id, payload)


@router.post('/{project_id}/batch-generate', response_model=JobStatusOut)
def batch_generate(project_id: UUID, db: Session = Depends(get_db)) -> JobStatusOut:
    return ProjectService(db).submit_batch_generate(project_id)
