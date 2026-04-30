import uuid
from datetime import UTC, datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AudioOutput(Base):
    __tablename__ = 'audio_outputs'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('audio_jobs.id'), nullable=False)
    source_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('audio_jobs.id'))
    artifact_id: Mapped[str | None] = mapped_column(String(120), index=True)
    artifact_type: Mapped[str | None] = mapped_column(String(50))
    output_type: Mapped[str] = mapped_column(String(50), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    public_url: Mapped[str | None] = mapped_column(Text)
    mime_type: Mapped[str | None] = mapped_column(String(120))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    waveform_json: Mapped[dict | None] = mapped_column(JSONB)
    checksum: Mapped[str | None] = mapped_column(String(128))
    input_hash: Mapped[str | None] = mapped_column(String(128))
    provider: Mapped[str | None] = mapped_column(String(120))
    model_version: Mapped[str | None] = mapped_column(String(120))
    template_version: Mapped[str | None] = mapped_column(String(120))
    runtime_version: Mapped[str | None] = mapped_column(String(120))
    generation_mode: Mapped[str] = mapped_column(String(32), nullable=False, default='unknown')
    provider_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    audio_contains_signal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    signal_rms: Mapped[int | None] = mapped_column(Integer)
    signal_peak: Mapped[int | None] = mapped_column(Integer)
    quality_report: Mapped[dict | None] = mapped_column(JSONB)
    promotion_status: Mapped[str] = mapped_column(String(50), nullable=False, default='generated')
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
