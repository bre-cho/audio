from pydantic import BaseModel, Field


class SFXPrompt(BaseModel):
    prompt: str = Field(min_length=3)
    duration_sec: float = Field(default=4, ge=0.5, le=30)
    style: str = "cinematic"
    loopable: bool = False


class SFXGenerationService:
    def generate(self, payload: SFXPrompt) -> dict:
        raise NotImplementedError("Wire prompt-to-sound-effect provider before enabling")
