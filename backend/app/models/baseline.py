import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Baseline(Base):
    __tablename__ = "baselines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    baseline_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    artifact_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    baseline_type: Mapped[str] = mapped_column(String(40), nullable=False)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    approved_by: Mapped[str] = mapped_column(String(120), nullable=False)
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    replay_schedule: Mapped[str] = mapped_column(String(40), nullable=False, default="nightly")
    drift_budget_policy: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="standby")
    lifecycle_state: Mapped[str] = mapped_column(String(40), nullable=False, default="candidate")
    control_baseline_id: Mapped[str | None] = mapped_column(String(120))
    rollback_baseline_id: Mapped[str | None] = mapped_column(String(120))
    canary_traffic_percentage: Mapped[int | None] = mapped_column(Integer)
    canary_window_minutes: Mapped[int | None] = mapped_column(Integer)
    segment_coverage: Mapped[dict | None] = mapped_column(JSONB)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))