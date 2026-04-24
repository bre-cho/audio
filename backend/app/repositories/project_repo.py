from uuid import UUID
from sqlalchemy.orm import Session
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: ProjectCreate, user_id: UUID) -> Project:
        project = Project(user_id=user_id, **payload.model_dump())
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def list(self) -> list[Project]:
        return self.db.query(Project).order_by(Project.created_at.desc()).limit(100).all()

    def get(self, project_id: UUID) -> Project | None:
        return self.db.query(Project).filter(Project.id == project_id).one_or_none()

    def update(self, project_id: UUID, payload: ProjectUpdate) -> Project | None:
        project = self.get(project_id)
        if not project:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project
