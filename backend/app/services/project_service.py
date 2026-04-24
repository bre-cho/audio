import uuid
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.script_asset import ScriptAsset
from app.repositories.job_repo import JobRepository
from app.repositories.project_repo import ProjectRepository
from app.schemas.job import JobStatusOut
from app.schemas.project import ProjectCreate, ProjectOut, ProjectScriptCreate, ProjectUpdate
from app.workers.audio_tasks import enqueue_batch_job


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectRepository(db)
        self.jobs = JobRepository(db)
        self.default_user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')

    def create_project(self, payload: ProjectCreate) -> ProjectOut:
        return ProjectOut.model_validate(self.repo.create(payload, self.default_user_id))

    def list_projects(self) -> list[ProjectOut]:
        return [ProjectOut.model_validate(p) for p in self.repo.list()]

    def get_project(self, project_id: UUID) -> ProjectOut | None:
        project = self.repo.get(project_id)
        return ProjectOut.model_validate(project) if project else None

    def update_project(self, project_id: UUID, payload: ProjectUpdate) -> ProjectOut | None:
        project = self.repo.update(project_id, payload)
        return ProjectOut.model_validate(project) if project else None

    def add_script(self, project_id: UUID, payload: ProjectScriptCreate) -> dict:
        asset = ScriptAsset(project_id=project_id, user_id=self.default_user_id, **payload.model_dump())
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return {'script_asset_id': str(asset.id)}

    def submit_batch_generate(self, project_id: UUID) -> JobStatusOut:
        job = self.jobs.create(user_id=self.default_user_id, job_type='batch', request_json={'project_id': str(project_id)}, project_id=project_id)
        enqueue_batch_job(str(job.id))
        return JobStatusOut.model_validate(job)
