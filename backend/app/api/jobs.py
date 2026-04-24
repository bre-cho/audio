from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.job import JobStatusOut
from app.services.job_service import JobService, UnsupportedRetryJobTypeError

router = APIRouter()


@router.get('', response_model=list[JobStatusOut])
def list_jobs(db: Session = Depends(get_db)) -> list[JobStatusOut]:
    return JobService(db).list_jobs()


@router.get('/{job_id}', response_model=JobStatusOut)
def get_job(job_id: UUID, db: Session = Depends(get_db)) -> JobStatusOut:
    job = JobService(db).get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return job


@router.post('/{job_id}/retry', response_model=JobStatusOut)
def retry_job(job_id: UUID, db: Session = Depends(get_db)) -> JobStatusOut:
    try:
        return JobService(db).retry_job(job_id)
    except UnsupportedRetryJobTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ValueError:
        raise HTTPException(status_code=404, detail='Job not found')
