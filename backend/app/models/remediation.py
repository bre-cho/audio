import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LastSafePolicy(Base):
    __tablename__ = "last_safe_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_version: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    recorded_by: Mapped[str] = mapped_column(String(120), nullable=False, default="system")
    evidence_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class Runbook(Base):
    __tablename__ = "runbooks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    runbook_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    root_cause_hint: Mapped[str] = mapped_column(String(500), nullable=False)
    owner: Mapped[str] = mapped_column(String(120), nullable=False)
    verification_command: Mapped[str] = mapped_column(String(500), nullable=False)
    steps: Mapped[list] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class RemediationRecord(Base):
    __tablename__ = "remediation_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    remediation_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    trigger_source: Mapped[str] = mapped_column(String(80), nullable=False)
    runbook_id: Mapped[str] = mapped_column(String(120), nullable=False)
    action_plan: Mapped[list] = mapped_column(JSONB, nullable=False)
    auto_apply_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    risk_level: Mapped[str] = mapped_column(String(40), nullable=False)
    blast_radius_estimate: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False)
    execution_status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")
    verification_status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")
    human_override_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approval_tier: Mapped[str] = mapped_column(String(40), nullable=False)
    execution_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )