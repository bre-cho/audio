from fastapi import APIRouter

router = APIRouter(prefix='/sound-effects')


@router.get('/status')
def sound_effects_status() -> dict:
    return {
        'feature': 'sound_effects',
        'feature_status': 'partial',
        'reason': 'Basic DSP effects exist, but provider-backed SFX engine is not production-ready',
    }
