# PATCH ORDER — P0 → P7

## P0 — Truthful Runtime Guard

Files:
- `backend/app/core/provider_policy.py`
- `backend/app/services/audio_quality_gate.py`
- `backend/app/api/system_capabilities.py`

Actions:
1. Add env flags:
   - `PROVIDER_STRICT_MODE=true`
   - `ALLOW_PLACEHOLDER_AUDIO=false`
   - `BLOCK_INTERNAL_GENVOICE_IN_PROD=true`
2. Reject `internal_genvoice` in production.
3. Reject artifacts with silence / zero RMS / invalid duration.

## P1 — Capability Registry + Voice Studio Core

Files:
- `backend/app/services/provider_capability_registry.py`
- `backend/app/models/voice_model.py`
- `backend/app/models/voice_recipe.py`
- `backend/app/services/voice_library_service.py`
- `backend/app/services/voice_design_service.py`
- `backend/app/api/voice_library.py`
- `backend/app/api/voice_design.py`

Actions:
1. Register providers and supported modules.
2. Store voice profiles and design recipes.
3. Block route when capability missing.

## P2 — Clone Mode + RVC Upload

Files:
- `backend/app/services/clone_mode_service.py`
- `backend/app/services/rvc_model_service.py`
- `backend/app/services/voice_consent_service.py`

Modes:
- `instant_clone`
- `professional_clone`
- `rvc_upload`

## P3 — Voice Changer Engine

Files:
- `backend/app/services/voice_conversion_engine.py`
- `backend/app/services/formant_preservation.py`
- `backend/app/services/speaker_similarity_service.py`
- `backend/app/api/voice_changer.py`

Must output:
- similarity_score
- naturalness_score
- artifact_score
- clipping_detected
- silence_detected

## P4 — SFX + BGM

Files:
- `backend/app/services/sfx_generation_service.py`
- `backend/app/services/bgm_generation_service.py`
- `backend/app/services/audio_mixer_service.py`
- `backend/app/api/sound_effects.py`
- `backend/app/api/bgm.py`

## P5 — Podcast Generator

Files:
- `backend/app/services/podcast_script_parser.py`
- `backend/app/services/speaker_casting_service.py`
- `backend/app/services/podcast_timeline_service.py`
- `backend/app/services/podcast_mixdown_service.py`
- `backend/app/api/podcast.py`

Flow:
`script → speaker detection → voice assignment → TTS per speaker → intro/outro/BGM → ducking → loudness normalize → final mix`

## P6 — STT / Subtitle / Translation

Files:
- `backend/app/services/stt_service.py`
- `backend/app/services/subtitle_export_service.py`
- `backend/app/services/voice_translate_service.py`
- `backend/app/api/transcription.py`
- `backend/app/api/localization.py`

Outputs:
- transcript.json
- subtitles.srt
- subtitles.vtt
- segments.json

## P7 — Frontend Studio Dashboard

Files:
- `frontend/src/api/audioStudio.ts`
- `frontend/src/pages/AudioStudioPage.tsx`
- `frontend/src/components/CapabilityBadge.tsx`

UI sections:
- Studio Overview
- Voice Library
- Voice Design
- TTS
- Clone
- Changer
- SFX/BGM
- Podcast
- Enhancer/Noise Reducer
- STT/Localization
