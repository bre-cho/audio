"""SQLAlchemy ORM model for persisted voice design recipes."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VoiceRecipeDB(Base):
    __tablename__ = "voice_recipes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False, default="en-US")
    gender: Mapped[str | None] = mapped_column(String(50))
    age: Mapped[str | None] = mapped_column(String(50))
    style: Mapped[str] = mapped_column(String(100), nullable=False, default="narration")
    emotion: Mapped[str] = mapped_column(String(100), nullable=False, default="calm")
    speed: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    pitch: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    provider: Mapped[str] = mapped_column(String(100), nullable=False, default="elevenlabs")
    extra_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
