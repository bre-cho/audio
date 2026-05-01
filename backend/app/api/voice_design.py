from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.voice_recipe import VoiceRecipeCreate
from app.services.voice_design_service import VoiceDesignService

router = APIRouter(prefix="/voice-design", tags=["Voice Design"])


@router.get("/recipes")
def list_recipes(db: Session = Depends(get_db)):
    return {"items": VoiceDesignService(db).list_recipes()}


@router.post("/recipes")
def create_recipe(payload: VoiceRecipeCreate, db: Session = Depends(get_db)):
    return VoiceDesignService(db).create_recipe(payload)
