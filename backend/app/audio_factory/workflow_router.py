from __future__ import annotations

from app.audio_factory.schemas import AudioTaskRequest, AudioWorkflowType


class AudioWorkflowRouter:
    def resolve(self, task: AudioTaskRequest) -> dict:
        if task.workflow_type == AudioWorkflowType.TTS_GENERATE:
            return {
                "handler": "tts_generate",
                "requires_text": True,
                "artifact_type": "audio",
                "expected_outputs": ["preview", "output"],
            }

        if task.workflow_type == AudioWorkflowType.TTS_PREVIEW:
            return {
                "handler": "tts_preview",
                "requires_text": True,
                "artifact_type": "audio",
                "expected_outputs": ["preview"],
            }

        if task.workflow_type == AudioWorkflowType.NARRATION:
            return {
                "handler": "narration",
                "requires_text": True,
                "artifact_type": "audio",
                "expected_outputs": ["preview", "output"],
            }

        if task.workflow_type == AudioWorkflowType.CONVERSATION:
            return {
                "handler": "conversation",
                "requires_conversation_content": True,
                "artifact_type": "audio",
                "expected_outputs": ["preview", "output"],
            }

        if task.workflow_type == AudioWorkflowType.CLONE_PREVIEW:
            return {
                "handler": "clone_preview",
                "artifact_type": "audio",
                "expected_outputs": ["clone_preview"],
            }

        raise ValueError(f"Unsupported workflow_type={task.workflow_type}")

    def validate_task_shape(self, task: AudioTaskRequest) -> None:
        spec = self.resolve(task)
        payload = task.request_json or {}

        text = task.text or payload.get("text") or payload.get("raw_script")
        script = task.script or payload.get("script")
        conversation_turns = (
            task.conversation_turns
            or payload.get("conversation_turns")
            or payload.get("script")
        )

        if spec.get("requires_text") and not text and not script:
            raise ValueError(f"{task.workflow_type} requires text or script")

        if spec.get("requires_conversation_content") and not conversation_turns and not script and not text:
            raise ValueError(f"{task.workflow_type} requires conversation_turns, script, or text")
