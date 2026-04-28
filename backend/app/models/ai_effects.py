"""AI Effects models for audio processing."""
import uuid
from datetime import datetime, UTC
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class AudioEffect(Base):
    """Store audio effect presets and configurations."""
    __tablename__ = 'audio_effects'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    effect_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # echo, reverb, eq, etc.
    description: Mapped[str | None] = mapped_column(Text)
    default_params: Mapped[dict] = mapped_column(JSONB, nullable=False)  # {delay_ms, feedback_ratio, etc.}
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class UserAudioEffectPreset(Base):
    """Store user's saved audio effect presets."""
    __tablename__ = 'user_audio_effect_presets'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    effect_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('audio_effects.id'), nullable=False)
    preset_name: Mapped[str] = mapped_column(String(150), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False)  # custom parameters for this preset
    is_public: Mapped[bool] = mapped_column(default=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
