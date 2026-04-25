import uuid
from datetime import datetime, UTC
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class AudioJob(Base):
    __tablename__ = 'audio_jobs'
    __table_args__ = (
        UniqueConstraint('user_id', 'job_type', 'idempotency_key', name='uq_audio_jobs_user_job_type_idempotency_key'),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('projects.id'))
    script_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('script_assets.id'))
    provider_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('providers.id'))
    voice_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('voices.id'))
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    workflow_type: Mapped[str] = mapped_column(String(50), nullable=False, default='unknown')
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='queued')
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    request_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    runtime_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error_code: Mapped[str | None] = mapped_column(String(120))
    idempotency_key: Mapped[str | None] = mapped_column(String(120), index=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    preview_url: Mapped[str | None] = mapped_column(Text)
    output_url: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
