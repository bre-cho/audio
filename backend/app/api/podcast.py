import base64
import binascii

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from app.audio_engines.podcast.podcast_mixer import MixerSegment, mix_podcast_wav
from app.services.podcast_script_parser import PodcastScriptParser
from app.services.speaker_casting_service import SpeakerCastingService
from app.services.podcast_timeline_service import PodcastTimelineService

router = APIRouter(prefix="/podcast", tags=["Podcast"])


class PodcastGenerateRequest(BaseModel):
    title: str
    script: str
    voice_map: dict[str, str]
    bgm: dict | None = None
    loudness_target_lufs: float = -16


class PodcastMixSegment(BaseModel):
    audio_b64: str | None = None
    speaker: str = ""
    pause_after_ms: int = 500


class PodcastMixRequest(BaseModel):
    title: str
    segments: list[PodcastMixSegment]


@router.get("/status")
def podcast_status():
    return {
        "feature": "podcast",
        "feature_status": "active",
        "mix_mode": "single_file_inline_b64",
    }


@router.post("/mix")
def mix_podcast(payload: PodcastMixRequest):
    if not payload.segments:
        raise HTTPException(status_code=400, detail="segments must not be empty")

    mixer_segments: list[MixerSegment] = []
    for i, seg in enumerate(payload.segments):
        if not seg.audio_b64:
            raise HTTPException(status_code=400, detail=f"segment[{i}] missing audio_b64")
        try:
            wav_bytes = base64.b64decode(seg.audio_b64, validate=True)
        except (ValueError, binascii.Error):
            raise HTTPException(status_code=400, detail=f"segment[{i}] invalid audio_b64")

        mixer_segments.append(
            MixerSegment(audio_wav=wav_bytes, speaker=seg.speaker, pause_after_ms=seg.pause_after_ms)
        )

    _mixed_wav, mix_report = mix_podcast_wav(segments=mixer_segments)
    return {"status": "ok", "title": payload.title, "mix_report": mix_report}


@router.post("/generate")
def generate_podcast(payload: PodcastGenerateRequest):
    parsed = PodcastScriptParser().parse(payload.script)
    speakers = sorted({line.speaker for line in parsed})
    cast = SpeakerCastingService().cast(speakers, payload.voice_map)
    timeline = PodcastTimelineService().build(parsed, cast)
    return {"status": "planned", "title": payload.title, "timeline": timeline, "next": "wire_tts_and_mixdown_worker"}
