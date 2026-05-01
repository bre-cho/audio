# 02 — Patch Order P0 → P7

## P0 — Truth Completion
Files:
```txt
backend/app/services/feature_execution_guard.py
backend/app/api/bgm.py
backend/app/api/sound_effects.py
backend/app/api/transcription.py
backend/app/api/localization.py
backend/app/api/voice_changer.py
backend/tests/test_no_fake_queued_routes.py
```

## P1 — Provider Unification
```txt
backend/app/providers/unified_provider_registry.py
backend/app/services/provider_runtime.py
backend/tests/test_provider_single_source.py
```

## P2 — TTS + Clone Hardening
```txt
backend/app/services/audio_decode_service.py
backend/app/services/provider_cost_service.py
backend/app/services/tts_generation_service.py
backend/app/services/voice_sample_qc_service.py
backend/app/services/voice_clone_lifecycle_service.py
backend/app/api/voice_clone_lifecycle.py
backend/tests/test_tts_clone_hardening.py
```

## P3 — Voice Changer
```txt
backend/app/audio_engines/voice_changer/rvc_adapter.py
backend/app/audio_engines/voice_changer/openvoice_adapter.py
backend/app/services/voice_conversion_job_service.py
backend/app/services/voice_conversion_quality_gate.py
backend/tests/test_voice_changer_provider_required.py
```

## P4 — Enhancer / Noise Reducer QA
```txt
backend/app/services/audio_enhancement_quality_service.py
```

## P5 — SFX / BGM
```txt
backend/app/audio_engines/sound_effects/elevenlabs_sfx_adapter.py
backend/app/audio_engines/bgm/replicate_musicgen_adapter.py
backend/app/services/sfx_bgm_job_service.py
backend/tests/test_sfx_bgm_provider_gate.py
```

## P6 — Podcast
```txt
backend/app/services/podcast_episode_builder.py
backend/app/services/podcast_tts_orchestrator.py
backend/app/services/podcast_ducking_service.py
backend/app/services/podcast_export_service.py
backend/app/workers/podcast_tasks.py
backend/tests/test_podcast_episode_builder.py
```

## P7 — Frontend + Verify
```txt
frontend/src/api/audioCapabilities.ts
frontend/src/components/audio/CapabilityAwareToolCard.tsx
frontend/src/components/audio/AudioJobProgress.tsx
backend/scripts/verify_audio_v3.sh
```
