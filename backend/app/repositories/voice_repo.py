from uuid import UUID
from sqlalchemy.orm import Session
from app.models.voice import Voice
from app.schemas.voice import VoiceListFilters, VoiceUpdate


class VoiceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, filters: VoiceListFilters) -> list[Voice]:
        query = self.db.query(Voice)
        if filters.language_code:
            query = query.filter(Voice.language_code == filters.language_code)
        if filters.source_type:
            query = query.filter(Voice.source_type == filters.source_type)
        return query.limit(100).all()

    def get(self, voice_id: UUID) -> Voice | None:
        return self.db.query(Voice).filter(Voice.id == voice_id).one_or_none()

    def update(self, voice_id: UUID, payload: VoiceUpdate) -> Voice | None:
        voice = self.get(voice_id)
        if not voice:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(voice, field, value)
        self.db.add(voice)
        self.db.commit()
        self.db.refresh(voice)
        return voice
