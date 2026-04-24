import uuid
from sqlalchemy.orm import Session
from app.models.audio_job import AudioJob


class JobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, user_id: uuid.UUID, job_type: str, request_json: dict, project_id=None, script_asset_id=None, voice_id=None) -> AudioJob:
        job = AudioJob(
            user_id=user_id,
            job_type=job_type,
            request_json=request_json,
            project_id=project_id,
            script_asset_id=script_asset_id,
            voice_id=voice_id,
            status='queued',
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def list(self) -> list[AudioJob]:
        return self.db.query(AudioJob).order_by(AudioJob.created_at.desc()).limit(100).all()

    def get(self, job_id) -> AudioJob | None:
        return self.db.query(AudioJob).filter(AudioJob.id == job_id).one_or_none()
