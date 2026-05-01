from fastapi import APIRouter
from pydantic import BaseModel
from app.services.podcast_production_service import mix_podcast_from_wav_clips

router = APIRouter()


class PodcastClipPayload(BaseModel):
    path: str
    start_sec: float = 0
    gain: float = 1


class PodcastMixRequest(BaseModel):
    clips: list[PodcastClipPayload]
    output_path: str = "artifacts/podcast/final_mix.wav"


@router.post("/mixdown")
def podcast_mixdown_v2(payload: PodcastMixRequest):
    return mix_podcast_from_wav_clips([c.model_dump() for c in payload.clips], payload.output_path)
