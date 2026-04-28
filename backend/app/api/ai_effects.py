"""API routes for audio effects."""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Query
from uuid import UUID
from sqlalchemy.orm import Session
from app.api.deps import AuthContext, get_current_user_id, get_db, require_scopes
from app.core.storage import StorageService
from app.schemas.ai_effects import (
    AudioEffectOut,
    UserAudioEffectPresetOut,
)
from app.schemas.job import JobStatusOut
from app.services.ai_effects_service import AudioEffectsService


router = APIRouter(prefix='/ai-effects', tags=['ai-effects'])


@router.get('/effects', response_model=list[AudioEffectOut])
def list_effects(db: Session = Depends(get_db)):
    """Get all available audio effects."""
    service = AudioEffectsService(db)
    effects = service.get_all_effects()
    return effects


@router.get('/presets', response_model=list[UserAudioEffectPresetOut])
def list_user_presets(
    db: Session = Depends(get_db),
    user_id=Depends(get_current_user_id),
):
    """Get user's saved effect presets."""
    service = AudioEffectsService(db)
    presets = service.get_user_presets(user_id)
    return presets


@router.post('/presets', response_model=UserAudioEffectPresetOut)
def create_preset(
    effect_id: UUID,
    preset_name: str,
    parameters: dict,
    is_public: bool = False,
    db: Session = Depends(get_db),
    user_id=Depends(get_current_user_id),
):
    """Save a custom effect preset."""
    service = AudioEffectsService(db)
    preset = service.create_user_preset(user_id, effect_id, preset_name, parameters, is_public)
    return preset


@router.delete('/presets/{preset_id}')
def delete_preset(preset_id: UUID, db: Session = Depends(get_db)):
    """Delete a user preset."""
    service = AudioEffectsService(db)
    service.delete_preset(preset_id)
    return {'status': 'deleted'}


@router.post('/apply', response_model=JobStatusOut)
async def apply_effect(
    file: UploadFile = File(...),
    effect_type: str = Query(..., description="echo, reverb, or eq"),
    parameters: str = Query(default='{}', description="JSON string of effect parameters"),
    db: Session = Depends(get_db),
    user_id=Depends(get_current_user_id),
):
    """Apply audio effect to uploaded file.
    
    Parameters vary by effect type:
    - echo: {delay_ms: int, feedback_ratio: float}
    - reverb: {room_size: float, wet: float}
    - eq: {bass_db: float, mid_db: float, treble_db: float}
    """
    # Validate effect type
    valid_effects = ['echo', 'reverb', 'eq']
    if effect_type not in valid_effects:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid effect type. Must be one of: {', '.join(valid_effects)}"
        )
    
    # Parse parameters
    import json
    try:
        params = json.loads(parameters)
    except json.JSONDecodeError:
        params = {}
    
    # Store uploaded file
    storage = StorageService()
    file_bytes = await file.read()
    stored = storage.put_bytes(
        key=f"effects/{user_id}/input-{file.filename}",
        data=file_bytes,
        content_type=file.content_type or 'audio/mpeg'
    )
    
    # Create effect job
    service = AudioEffectsService(db)
    try:
        job = service.apply_effect(
            user_id=user_id,
            effect_type=effect_type,
            parameters=params,
            input_file_key=stored.key
        )
    except ValueError as e:
        # Handle insufficient credits
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(e)
        )
    
    return JobStatusOut.model_validate(job)


@router.post('/init-defaults')
def initialize_default_effects(
    db: Session = Depends(get_db),
    _: AuthContext = Depends(require_scopes('ai-effects.init-defaults')),
):
    """Initialize default audio effects (admin only)."""
    service = AudioEffectsService(db)
    service.initialize_default_effects()
    return {'status': 'initialized', 'message': 'Default audio effects created'}
