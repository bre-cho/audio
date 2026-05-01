# 06 — Dev Notes File-by-File

## Replacement files

These files intentionally replace current weak route implementations:

```txt
backend/app/api/bgm.py
backend/app/api/sound_effects.py
backend/app/api/transcription.py
backend/app/api/localization.py
backend/app/api/voice_changer.py
```

Reason: current versions can return `queued` even when no real job/engine is created.

## Additive files

All other files are additive scaffolds/gates. They should not break existing stable paths unless imported by the replacement routes.

## Router note

Add this router after apply if wanted:

```python
from app.api import voice_clone_lifecycle
api_router.include_router(voice_clone_lifecycle.router)
```

## Capability env note

`voice_translation` is used by localization. Add to `CAPABILITY_ENV` in `provider_capability_gate_v2.py` if not present:

```python
"voice_translation": ("VOICE_TRANSLATION_PROVIDER", None),
```
