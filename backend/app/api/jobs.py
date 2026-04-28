import json
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.job import JobStatusOut
from app.services.job_service import JobService, UnsupportedRetryJobTypeError

router = APIRouter()


@router.get('', response_model=list[JobStatusOut])
def list_jobs(db: Session = Depends(get_db)) -> list[JobStatusOut]:
    return JobService(db).list_jobs()


@router.get('/stream')
def stream_jobs(db: Session = Depends(get_db)) -> StreamingResponse:
    service = JobService(db)

    def generate():
        last_payload = None
        yield 'retry: 3000\n\n'
        while True:
            payload = [job.model_dump(mode='json') for job in service.list_jobs()]
            serialized = json.dumps(payload, default=str, separators=(',', ':'))
            if serialized != last_payload:
                yield f'event: jobs\ndata: {serialized}\n\n'
                last_payload = serialized
            time.sleep(2)

    return StreamingResponse(
        generate(),
        media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'},
    )


@router.get('/{job_id}', response_model=JobStatusOut)
def get_job(job_id: UUID, db: Session = Depends(get_db)) -> JobStatusOut:
    job = JobService(db).get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Khong tim thay job')
    return job


@router.post('/{job_id}/retry', response_model=JobStatusOut)
def retry_job(job_id: UUID, db: Session = Depends(get_db)) -> JobStatusOut:
    try:
        return JobService(db).retry_job(job_id)
    except UnsupportedRetryJobTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ValueError:
        raise HTTPException(status_code=404, detail='Khong tim thay job')
