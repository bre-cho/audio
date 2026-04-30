from fastapi import APIRouter

router = APIRouter(prefix='/audio-quality')


@router.get('/status')
def audio_quality_status() -> dict:
    return {
        'feature': 'audio_quality',
        'feature_status': 'partial',
        'reason': 'Signal validator exists; full LUFS/SNR/clipping report engine not wired yet',
    }
