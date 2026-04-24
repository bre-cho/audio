from fastapi import APIRouter
from app.core.config import settings
from app.schemas.provider import ProviderOut

router = APIRouter()


@router.get('', response_model=list[ProviderOut])
async def list_providers() -> list[ProviderOut]:
    return [
        ProviderOut(code='elevenlabs', name='ElevenLabs', status='active'),
        ProviderOut(code='minimax', name='Minimax', status='active'),
        ProviderOut(code='internal_genvoice', name='Internal GenVoice', status='disabled'),
    ]
