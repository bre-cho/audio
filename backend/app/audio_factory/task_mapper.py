from __future__ import annotations

from uuid import UUID

from app.audio_factory.schemas import AudioTaskRequest, AudioWorkflowType
from app.schemas.conversation import ConversationGenerateRequest
from app.schemas.tts import TTSGenerateRequest, TTSPreviewRequest
from app.schemas.voice_clone import VoiceClonePreviewRequest


def build_tts_generate_task(payload: TTSGenerateRequest) -> AudioTaskRequest:
    request_json = payload.model_dump(mode="json", exclude_none=True)
    return AudioTaskRequest(
        workflow_type=AudioWorkflowType.TTS_GENERATE,
        request_json=request_json,
        text=payload.text,
        voice_id=str(payload.voice_id) if payload.voice_id else None,
        provider=payload.provider or "internal_genvoice",
    )


def build_tts_preview_task(payload: TTSPreviewRequest) -> AudioTaskRequest:
    request_json = payload.model_dump(mode="json", exclude_none=True)
    return AudioTaskRequest(
        workflow_type=AudioWorkflowType.TTS_PREVIEW,
        request_json=request_json,
        text=payload.text,
        voice_id=str(payload.voice_id) if payload.voice_id else None,
        provider=payload.provider or "internal_genvoice",
    )


def build_audio_preview_task(*, text: str, voice: str = "default", provider: str | None = None, voice_id: str | None = None) -> AudioTaskRequest:
    request_json = {
        "text": text,
        "voice": voice,
    }
    if provider:
        request_json["provider"] = provider
    if voice_id:
        request_json["voice_id"] = voice_id

    return AudioTaskRequest(
        workflow_type=AudioWorkflowType.TTS_PREVIEW,
        request_json=request_json,
        text=text,
        voice_id=voice_id,
        provider=provider or "internal_genvoice",
    )


def build_audio_narration_task(
    *,
    text: str,
    voice_profile_id: str | None = None,
    provider: str | None = None,
    project_id: str | None = None,
) -> AudioTaskRequest:
    request_json = {
        "text": text,
    }
    if voice_profile_id:
        request_json["voice_profile_id"] = voice_profile_id
    if provider:
        request_json["provider"] = provider
    if project_id:
        request_json["project_id"] = project_id

    return AudioTaskRequest(
        workflow_type=AudioWorkflowType.NARRATION,
        request_json=request_json,
        text=text,
        voice_id=voice_profile_id,
        provider=provider or "internal_genvoice",
    )


def build_conversation_task(payload: ConversationGenerateRequest) -> AudioTaskRequest:
    conversation_turns = [line.model_dump(mode="json") for line in payload.script]
    request_json = payload.model_dump(mode="json", exclude_none=True)
    request_json["conversation_turns"] = conversation_turns
    return AudioTaskRequest(
        workflow_type=AudioWorkflowType.CONVERSATION,
        request_json=request_json,
        script=conversation_turns,
        conversation_turns=conversation_turns,
        provider="internal_genvoice",
    )


def build_clone_preview_task(voice_id: UUID, payload: VoiceClonePreviewRequest) -> AudioTaskRequest:
    request_json = payload.model_dump(mode="json", exclude_none=True)
    request_json["voice_id"] = str(voice_id)
    request_json["clone_source_key"] = str(voice_id)
    return AudioTaskRequest(
        workflow_type=AudioWorkflowType.CLONE_PREVIEW,
        request_json=request_json,
        text=payload.text,
        voice_id=str(voice_id),
        clone_source_key=str(voice_id),
        provider="internal_genvoice",
    )
