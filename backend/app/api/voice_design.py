from fastapi import APIRouter

router = APIRouter(prefix='/voice-design')


@router.get('/status')
def voice_design_status() -> dict:
    return {
        'feature': 'voice_design',
        'feature_status': 'disabled',
        'reason': 'Engine route added but backend service/worker not fully wired yet',
    }
