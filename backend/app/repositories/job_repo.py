import uuid
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.audio_job import AudioJob


class JobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: uuid.UUID,
        job_type: str,
        request_json: dict,
        project_id=None,
        script_asset_id=None,
        voice_id=None,
        workflow_type: str | None = None,
        idempotency_key: str | None = None,
    ) -> AudioJob:
        job = AudioJob(
            user_id=user_id,
            job_type=job_type,
            workflow_type=workflow_type or job_type,
            idempotency_key=idempotency_key,
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

    def get_by_idempotency_key(self, *, user_id: uuid.UUID, job_type: str, idempotency_key: str) -> AudioJob | None:
        return (
            self.db.query(AudioJob)
            .filter(
                AudioJob.user_id == user_id,
                AudioJob.job_type == job_type,
                AudioJob.idempotency_key == idempotency_key,
            )
            .one_or_none()
        )

    def create_or_get(
        self,
        *,
        user_id: uuid.UUID,
        job_type: str,
        request_json: dict,
        project_id=None,
        script_asset_id=None,
        voice_id=None,
        workflow_type: str | None = None,
        idempotency_key: str | None = None,
    ) -> tuple[AudioJob, bool]:
        if idempotency_key:
            existing = self.get_by_idempotency_key(
                user_id=user_id,
                job_type=job_type,
                idempotency_key=idempotency_key,
            )
            if existing is not None:
                return existing, False

        try:
            created = self.create(
                user_id=user_id,
                job_type=job_type,
                request_json=request_json,
                project_id=project_id,
                script_asset_id=script_asset_id,
                voice_id=voice_id,
                workflow_type=workflow_type,
                idempotency_key=idempotency_key,
            )
            return created, True
        except IntegrityError:
            # A concurrent request may have created the same idempotent job.
            self.db.rollback()
            if not idempotency_key:
                raise
            existing = self.get_by_idempotency_key(
                user_id=user_id,
                job_type=job_type,
                idempotency_key=idempotency_key,
            )
            if existing is None:
                raise
            return existing, False

    def list(self) -> list[AudioJob]:
        return self.db.query(AudioJob).order_by(AudioJob.created_at.desc()).limit(100).all()

    def get(self, job_id) -> AudioJob | None:
        return self.db.query(AudioJob).filter(AudioJob.id == job_id).one_or_none()
