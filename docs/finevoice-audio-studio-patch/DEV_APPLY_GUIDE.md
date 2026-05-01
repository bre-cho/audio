# DEV APPLY GUIDE

## 1. Copy files

Copy toàn bộ thư mục `backend/`, `frontend/`, `tests/`, `scripts/`, `schemas/` từ patch pack vào root repo.

## 2. Wire API router

Trong `backend/app/api/router.py`, thêm các router mới nếu chưa có:

```python
from app.api.system_capabilities import router as system_capabilities_router
from app.api.voice_library import router as voice_library_router
from app.api.voice_design import router as voice_design_router
from app.api.voice_changer import router as voice_changer_router
from app.api.sound_effects import router as sound_effects_router
from app.api.bgm import router as bgm_router
from app.api.podcast import router as podcast_router
from app.api.transcription import router as transcription_router
from app.api.localization import router as localization_router

api_router.include_router(system_capabilities_router)
api_router.include_router(voice_library_router)
api_router.include_router(voice_design_router)
api_router.include_router(voice_changer_router)
api_router.include_router(sound_effects_router)
api_router.include_router(bgm_router)
api_router.include_router(podcast_router)
api_router.include_router(transcription_router)
api_router.include_router(localization_router)
```

## 3. Wire env

Add to `.env.example`:

```env
PROVIDER_STRICT_MODE=true
ALLOW_PLACEHOLDER_AUDIO=false
BLOCK_INTERNAL_GENVOICE_IN_PROD=true
AUDIO_MIN_RMS=0.001
AUDIO_MIN_DURATION_SEC=0.25
```

## 4. Run migration

```bash
cd backend
alembic upgrade head
```

## 5. Run verify

```bash
bash scripts/ci/verify_finevoice_audio_studio_patch.sh
pytest tests/test_audio_quality_gate.py tests/test_provider_capability_registry.py
```
