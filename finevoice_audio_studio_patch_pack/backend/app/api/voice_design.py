from fastapi import APIRouter
from app.models.voice_recipe import VoiceRecipeCreate
from app.services.voice_design_service import VoiceDesignService

router = APIRouter(prefix="/api/voice-design", tags=["Voice Design"])
_service = VoiceDesignService()


@router.get("/recipes")
def list_recipes():
    return {"items": _service.list_recipes()}


@router.post("/recipes")
def create_recipe(payload: VoiceRecipeCreate):
    return _service.create_recipe(payload)
