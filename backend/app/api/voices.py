from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.repositories.voice_repo import VoiceRepository
from app.schemas.voice import VoiceListFilters, VoiceOut, VoiceUpdate

router = APIRouter()


@router.get('', response_model=list[VoiceOut])
def list_voices(
    provider: str | None = None,
    language_code: str | None = None,
    source_type: str | None = None,
    db: Session = Depends(get_db),
) -> list[VoiceOut]:
    repo = VoiceRepository(db)
    filters = VoiceListFilters(provider=provider, language_code=language_code, source_type=source_type)
    return repo.list(filters)


@router.get('/{voice_id}', response_model=VoiceOut)
def get_voice(voice_id: UUID, db: Session = Depends(get_db)) -> VoiceOut:
    repo = VoiceRepository(db)
    voice = repo.get(voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail='Voice not found')
    return voice


@router.patch('/{voice_id}', response_model=VoiceOut)
def update_voice(voice_id: UUID, payload: VoiceUpdate, db: Session = Depends(get_db)) -> VoiceOut:
    repo = VoiceRepository(db)
    voice = repo.update(voice_id, payload)
    if not voice:
        raise HTTPException(status_code=404, detail='Voice not found')
    return voice
