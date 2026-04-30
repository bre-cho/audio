from fastapi import APIRouter

router = APIRouter(prefix='/voice-changer')


@router.get('/status')
def voice_changer_status() -> dict:
    return {
        'feature': 'voice_changer',
        'feature_status': 'partial',
        'reason': 'Legacy pitch-shift flow exists; production conversion engine not wired',
    }
