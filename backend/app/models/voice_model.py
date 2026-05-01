from pydantic import BaseModel, Field
from typing import Optional


class VoiceProfile(BaseModel):
    voice_id: str
    provider: str
    name: str
    gender: Optional[str] = None
    language: str = "en-US"
    style: Optional[str] = None
    emotion: Optional[str] = None
    commercial_use: bool = False
    is_cloned: bool = False
    is_rvc_model: bool = False
    external_voice_id: Optional[str] = None


class VoiceProfileCreate(BaseModel):
    name: str
    provider: str = "elevenlabs"
    gender: Optional[str] = None
    language: str = "en-US"
    style: Optional[str] = None
    emotion: Optional[str] = None
    commercial_use: bool = False
