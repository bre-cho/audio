from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.audio_engines.sound_effects.sfx_provider_adapter import SFXProviderAdapter
from app.audio_engines.bgm.bgm_provider_adapter import BGMProviderAdapter

router = APIRouter()


class SFXRequest(BaseModel):
    prompt: str
    duration_sec: float = 4
    output_path: str = "artifacts/sfx/generated.wav"


class BGMRequest(BaseModel):
    prompt: str
    duration_sec: float = 30
    loopable: bool = False
    output_path: str = "artifacts/bgm/generated.wav"


@router.post("/sfx")
def generate_sfx_v2(payload: SFXRequest):
    try:
        return SFXProviderAdapter().generate(**payload.model_dump()).__dict__
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/bgm")
def generate_bgm_v2(payload: BGMRequest):
    try:
        return BGMProviderAdapter().generate(**payload.model_dump()).__dict__
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
