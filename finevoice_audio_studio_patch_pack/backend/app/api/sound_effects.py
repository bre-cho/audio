from fastapi import APIRouter, HTTPException
from app.services.sfx_generation_service import SFXPrompt
from app.services.provider_capability_registry import default_registry

router = APIRouter(prefix="/api/sound-effects", tags=["Sound Effects"])


@router.post("/generate")
def generate_sfx(payload: SFXPrompt, provider: str = "sfx_provider"):
    cap = default_registry().get(provider, "sound_effects")
    if cap.status != "ready":
        raise HTTPException(status_code=409, detail={"status": cap.status, "reason": cap.reason})
    return {"status": "queued", "prompt": payload.prompt}
