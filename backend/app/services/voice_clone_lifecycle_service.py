from __future__ import annotations

from app.services.real_clone_service import clone_voice_real
from app.services.voice_sample_qc_service import validate_clone_samples


class VoiceCloneLifecycleService:
    def create_clone(self, *, name: str, sample_paths: list[str], description: str | None = None, consent_proof_id: str | None = None) -> dict:
        if not consent_proof_id:
            raise RuntimeError("consent_proof_required")
        qc = validate_clone_samples(sample_paths)
        result = clone_voice_real(name=name, sample_paths=sample_paths, description=description)
        return {"status": "created", "qc": qc, **result}

    def poll_status(self, external_voice_id: str) -> dict:
        return {"status": "ready", "external_voice_id": external_voice_id}

    def delete_clone(self, external_voice_id: str) -> dict:
        from app.providers.elevenlabs import ElevenLabsProvider
        client = ElevenLabsProvider().client
        client.request("DELETE", f"/v1/voices/{external_voice_id}")
        return {"status": "deleted", "external_voice_id": external_voice_id}
