from uuid import uuid4
from app.models.voice_recipe import VoiceRecipe, VoiceRecipeCreate
from app.services.provider_capability_registry import default_registry


class VoiceDesignService:
    def __init__(self):
        self._recipes: dict[str, VoiceRecipe] = {}

    def create_recipe(self, payload: VoiceRecipeCreate) -> VoiceRecipe:
        default_registry().assert_ready(payload.provider, "tts", allow_degraded=False)
        recipe = VoiceRecipe(recipe_id=f"recipe_{uuid4().hex[:12]}", **payload.model_dump())
        self._recipes[recipe.recipe_id] = recipe
        return recipe

    def list_recipes(self) -> list[VoiceRecipe]:
        return list(self._recipes.values())
