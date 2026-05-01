from fastapi import APIRouter
from pydantic import BaseModel
from app.audio_engines.qa.audio_quality_metrics import audio_quality_metrics

router = APIRouter()


class AudioQualityRequest(BaseModel):
    path: str


@router.post("/analyze")
def analyze_audio_quality_v2(payload: AudioQualityRequest):
    return audio_quality_metrics(payload.path)
