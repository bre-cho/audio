from pydantic import BaseModel, Field
from typing import Optional


class VoiceRecipe(BaseModel):
    recipe_id: str
    name: str
    language: str = "en-US"
    gender: Optional[str] = None
    age: Optional[str] = None
    style: str = "narration"
    emotion: str = "calm"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-12.0, le=12.0)
    provider: str = "elevenlabs"


class VoiceRecipeCreate(BaseModel):
    name: str
    language: str = "en-US"
    gender: Optional[str] = None
    age: Optional[str] = None
    style: str = "narration"
    emotion: str = "calm"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-12.0, le=12.0)
    provider: str = "elevenlabs"
