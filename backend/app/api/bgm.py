from fastapi import APIRouter, HTTPException
from app.services.bgm_generation_service import BGMPrompt
from app.services.provider_capability_registry import default_registry

router = APIRouter(prefix="/bgm", tags=["BGM"])


@router.post("/generate")
def generate_bgm(payload: BGMPrompt, provider: str = "bgm_provider"):
    cap = default_registry().get(provider, "bgm")
    if cap.status != "ready":
        raise HTTPException(status_code=409, detail={"status": cap.status, "reason": cap.reason})
    return {"status": "queued", "prompt": payload.prompt}
