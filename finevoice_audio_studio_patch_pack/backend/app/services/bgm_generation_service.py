from pydantic import BaseModel, Field


class BGMPrompt(BaseModel):
    prompt: str = Field(min_length=3)
    duration_sec: float = Field(default=30, ge=2, le=600)
    mood: str = "cinematic"
    loopable: bool = True


class BGMGenerationService:
    def generate(self, payload: BGMPrompt) -> dict:
        raise NotImplementedError("Wire BGM provider before enabling")
