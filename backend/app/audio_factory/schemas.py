from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AudioWorkflowType(str, Enum):
    TTS_GENERATE = "tts_generate"
    TTS_PREVIEW = "tts_preview"
    NARRATION = "narration"
    CONVERSATION = "conversation"
    CLONE_PREVIEW = "clone_preview"


class AudioTaskRequest(BaseModel):
    workflow_type: AudioWorkflowType
    source_job_id: str | None = None
    request_json: dict[str, Any] = Field(default_factory=dict)

    text: str | None = None
    script: Any | None = None
    conversation_turns: list[dict[str, Any]] | list[Any] | None = None

    voice_id: str | None = None
    clone_source_key: str | None = None

    provider: str = "internal_genvoice"
    model_version: str | None = None
    template_version: str | None = None
    runtime_version: str | None = None

    input_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AudioArtifactContract(BaseModel):
    artifact_id: str
    artifact_type: str
    source_job_id: str
    job_id: str
    created_at: str | None = None

    storage_key: str
    path: str | None = None
    url: str | None = None
    public_url: str | None = None

    mime_type: str
    size_bytes: int
    checksum: str

    input_hash: str | None = None
    provider: str | None = None
    model_version: str | None = None
    template_version: str | None = None
    runtime_version: str | None = None

    waveform_json: dict[str, Any] | None = None
    contract_pass: bool = True
    lineage_pass: bool = True
    write_integrity_pass: bool = True
    replayability_pass: bool = False
    determinism_pass: bool = False
    drift_budget_pass: bool = False
    replayability_status: str = "pending"
    determinism_status: str = "pending"
    drift_budget_status: str = "pending"
    generation_mode: str = "unknown"
    provider_verified: bool = False
    audio_contains_signal: bool = False
    signal_rms: int | None = None
    signal_peak: int | None = None
    quality_report: dict[str, Any] | None = None
    promotion_status: str = "generated"
    promotion_reason: str | None = None
    checked_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AudioFactoryResult(BaseModel):
    success: bool
    workflow_type: AudioWorkflowType
    job_id: str
    artifacts: list[AudioArtifactContract] = Field(default_factory=list)
    preview_url: str | None = None
    output_url: str | None = None
    artifact_contract_version: str | None = None
    validation: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    incident: dict[str, Any] | None = None