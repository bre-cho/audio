"""Repository for persisted voice design recipes."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.voice_recipe_db import VoiceRecipeDB
from app.models.voice_recipe import VoiceRecipe, VoiceRecipeCreate


class VoiceRecipeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, recipe_id: str, payload: VoiceRecipeCreate) -> VoiceRecipeDB:
        row = VoiceRecipeDB(
            recipe_id=recipe_id,
            name=payload.name,
            language=payload.language,
            gender=payload.gender,
            age=payload.age,
            style=payload.style,
            emotion=payload.emotion,
            speed=payload.speed,
            pitch=payload.pitch,
            provider=payload.provider,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_all(self) -> list[VoiceRecipeDB]:
        return self.db.query(VoiceRecipeDB).order_by(VoiceRecipeDB.created_at.desc()).all()

    def get_by_recipe_id(self, recipe_id: str) -> VoiceRecipeDB | None:
        return self.db.query(VoiceRecipeDB).filter_by(recipe_id=recipe_id).one_or_none()

    @staticmethod
    def to_schema(row: VoiceRecipeDB) -> VoiceRecipe:
        return VoiceRecipe(
            recipe_id=row.recipe_id,
            name=row.name,
            language=row.language,
            gender=row.gender,
            age=row.age,
            style=row.style,
            emotion=row.emotion,
            speed=row.speed,
            pitch=row.pitch,
            provider=row.provider,
        )
