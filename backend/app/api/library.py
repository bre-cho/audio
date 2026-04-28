"""Public voice & effects library catalog — no auth required."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.voice import Voice
from app.services.ai_effects_service import AudioEffectsService

router = APIRouter(prefix="/library", tags=["library"])


@router.get("/voices")
def list_library_voices(
    language_code: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    gender: str | None = Query(default=None),
    quality_tier: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Public catalog of available voices. No authentication required."""
    q = db.query(Voice).filter(Voice.is_active == True)  # noqa: E712
    if language_code:
        q = q.filter(Voice.language_code == language_code)
    if source_type:
        q = q.filter(Voice.source_type == source_type)
    if gender:
        q = q.filter(Voice.gender == gender)
    if quality_tier:
        q = q.filter(Voice.quality_tier == quality_tier)
    voices = q.limit(limit).all()
    return [
        {
            "id": str(v.id),
            "name": v.name,
            "language_code": v.language_code,
            "gender": v.gender,
            "age_group": v.age_group,
            "tone_tags": v.tone_tags,
            "style_tags": v.style_tags,
            "source_type": v.source_type,
            "visibility": v.visibility,
            "quality_tier": v.quality_tier,
            "preview_url": v.preview_url,
            "avatar_url": v.avatar_url,
        }
        for v in voices
    ]


@router.get("/effects")
def list_library_effects(db: Session = Depends(get_db)) -> list[dict]:
    """Public catalog of available audio effects. No authentication required."""
    effects = AudioEffectsService(db).get_all_effects()
    return [
        {
            "id": str(e.id),
            "name": e.name,
            "effect_type": e.effect_type,
            "description": e.description,
            "default_params": e.default_params,
        }
        for e in effects
    ]


@router.get("/catalog")
def library_catalog(db: Session = Depends(get_db)) -> dict:
    """Unified catalog summary: voice count by source_type + effect count."""
    from sqlalchemy import func

    voice_counts = (
        db.query(Voice.source_type, func.count(Voice.id))
        .filter(Voice.is_active == True)  # noqa: E712
        .group_by(Voice.source_type)
        .all()
    )
    total_effects = AudioEffectsService(db).get_all_effects()
    return {
        "voices": {row[0] or "unknown": row[1] for row in voice_counts},
        "effects_count": len(total_effects),
    }
