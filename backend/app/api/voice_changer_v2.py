from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.audio_engines.voice_changer.conversion_adapter_v2 import VoiceConversionAdapterV2

router = APIRouter()


class VoiceChangeRequest(BaseModel):
    input_path: str
    target_voice_id: str
    output_path: str = "artifacts/voice_changer/converted.wav"


@router.post("/convert")
def convert_voice_v2(payload: VoiceChangeRequest):
    try:
        result = VoiceConversionAdapterV2().convert(input_path=payload.input_path, target_voice_id=payload.target_voice_id, output_path=payload.output_path)
        return result.__dict__
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
