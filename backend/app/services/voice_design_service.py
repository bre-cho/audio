from uuid import uuid4
from sqlalchemy.orm import Session
from app.models.voice_recipe import VoiceRecipe, VoiceRecipeCreate
from app.repositories.voice_recipe_repo import VoiceRecipeRepository
from app.services.provider_capability_registry import default_registry


class VoiceDesignService:
    """Manage voice design recipes, persisted to the database."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = VoiceRecipeRepository(db)

    def create_recipe(self, payload: VoiceRecipeCreate) -> VoiceRecipe:
        default_registry().assert_ready(payload.provider, "tts", allow_degraded=False)
        recipe_id = f"recipe_{uuid4().hex[:12]}"
        row = self._repo.create(recipe_id, payload)
        return VoiceRecipeRepository.to_schema(row)

    def list_recipes(self) -> list[VoiceRecipe]:
        rows = self._repo.list_all()
        return [VoiceRecipeRepository.to_schema(r) for r in rows]
