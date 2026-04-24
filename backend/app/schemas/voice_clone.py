from pydantic import BaseModel, Field


class VoiceCloneUploadResponse(BaseModel):
    file_id: str
    upload_url: str | None = None


class VoiceCloneCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    provider: str
    language_code: str
    gender: str | None = None
    sample_file_id: str
    denoise: bool = False
    consent_confirmed: bool


class VoiceClonePreviewRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)
