"""Pydantic schemas for AI Effects."""
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID


class AudioEffectOut(BaseModel):
    """Output schema for audio effect."""
    id: UUID
    name: str
    effect_type: str
    description: str | None = None
    default_params: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserAudioEffectPresetOut(BaseModel):
    """Output schema for user audio effect preset."""
    id: UUID
    preset_name: str
    effect_id: UUID
    parameters: dict
    is_public: bool
    usage_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplyAudioEffectRequest(BaseModel):
    """Request to apply audio effect to a file."""
    effect_type: str = Field(..., description="Type of effect: echo, reverb, eq")
    parameters: dict = Field(default_factory=dict, description="Effect parameters")
    # echo: {delay_ms: int, feedback_ratio: float}
    # reverb: {room_size: float, wet: float}
    # eq: {bass_db: float, mid_db: float, treble_db: float}


class ApplyAudioEffectResponse(BaseModel):
    """Response from applying audio effect."""
    job_id: str | UUID
    effect_type: str
    status: str
    created_time: datetime
    estimated_duration_seconds: float | None = None

    model_config = ConfigDict(from_attributes=True)
