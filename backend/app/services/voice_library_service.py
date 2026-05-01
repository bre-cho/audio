from uuid import uuid4
from app.models.voice_model import VoiceProfile, VoiceProfileCreate


class VoiceLibraryService:
    def __init__(self):
        self._voices: dict[str, VoiceProfile] = {}

    def create(self, payload: VoiceProfileCreate) -> VoiceProfile:
        voice = VoiceProfile(voice_id=f"voice_{uuid4().hex[:12]}", **payload.model_dump())
        self._voices[voice.voice_id] = voice
        return voice

    def list(self) -> list[VoiceProfile]:
        return list(self._voices.values())
