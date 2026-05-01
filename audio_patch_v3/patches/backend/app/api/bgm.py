from fastapi import APIRouter
from app.services.bgm_generation_service import BGMPrompt, BGMGenerationService
from app.services.feature_execution_guard import assert_capability_ready, not_implemented

router = APIRouter(prefix="/bgm", tags=["BGM"])


@router.post("/generate")
def generate_bgm(payload: BGMPrompt):
    state = assert_capability_ready("bgm")
    service = BGMGenerationService()
    try:
        result = service.generate(payload)
    except NotImplementedError:
        not_implemented("bgm", state.provider, "BGM provider adapter is not wired. Set BGM_PROVIDER to a supported provider and implement adapter.")
    return result
