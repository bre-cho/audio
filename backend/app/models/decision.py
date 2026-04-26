import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DecisionRecord(Base):
    __tablename__ = "decision_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    trigger_type: Mapped[str] = mapped_column(String(80), nullable=False)
    scenarios_considered: Mapped[list] = mapped_column(JSONB, nullable=False)
    selected_action: Mapped[str] = mapped_column(String(80), nullable=False)
    rejected_actions: Mapped[list | None] = mapped_column(JSONB)
    score_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False)
    selected_reason: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(120), nullable=False)
    decision_actor: Mapped[str] = mapped_column(String(40), nullable=False)
    execution_status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")
    outcome_tracking_id: Mapped[str] = mapped_column(String(120), nullable=False)
    prediction_json: Mapped[dict | None] = mapped_column(JSONB)
    actual_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )