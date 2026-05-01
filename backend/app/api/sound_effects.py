from fastapi import APIRouter, Depends
from app.core.rate_limit import rate_limit
from app.services.sfx_generation_service import SFXPrompt, SFXGenerationService
from app.services.feature_execution_guard import assert_capability_ready, not_implemented

router = APIRouter(prefix="/sound-effects", tags=["Sound Effects"])


@router.post("/generate")
def generate_sfx(
    payload: SFXPrompt,
    _rl: None = Depends(rate_limit(max_requests=30, window_seconds=60)),
):
    state = assert_capability_ready("sound_effects")
    service = SFXGenerationService()
    try:
        result = service.generate(payload)
    except NotImplementedError:
        not_implemented("sound_effects", state.provider, "SFX provider adapter is not wired. Set SFX_PROVIDER to a supported provider and implement adapter.")
    return result
