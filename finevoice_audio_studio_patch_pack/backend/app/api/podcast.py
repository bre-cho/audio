from pydantic import BaseModel
from fastapi import APIRouter
from app.services.podcast_script_parser import PodcastScriptParser
from app.services.speaker_casting_service import SpeakerCastingService
from app.services.podcast_timeline_service import PodcastTimelineService

router = APIRouter(prefix="/api/podcast", tags=["Podcast"])


class PodcastGenerateRequest(BaseModel):
    title: str
    script: str
    voice_map: dict[str, str]
    bgm: dict | None = None
    loudness_target_lufs: float = -16


@router.post("/generate")
def generate_podcast(payload: PodcastGenerateRequest):
    parsed = PodcastScriptParser().parse(payload.script)
    speakers = sorted({line.speaker for line in parsed})
    cast = SpeakerCastingService().cast(speakers, payload.voice_map)
    timeline = PodcastTimelineService().build(parsed, cast)
    return {"status": "planned", "title": payload.title, "timeline": timeline, "next": "wire_tts_and_mixdown_worker"}
