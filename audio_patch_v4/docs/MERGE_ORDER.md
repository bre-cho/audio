# Merge Order

## Phase 0 — API Canonicalization
- Add `api/canonical_routes.py`.
- Update main router to include canonical routes.
- Keep v1 endpoints only as deprecated wrappers.
- Add tests that fail when v1 or v2 returns fake `queued` without job id.

## Phase 1 — Provider Single Source
- Add `providers/provider_contract.py`.
- Add `providers/provider_registry_v4.py`.
- Move all capability checks through `ProviderRegistryV4.require()`.
- Mark old provider adapters deprecated.

## Phase 2 — TTS/Clone Lifecycle
- Add unified lifecycle service.
- Validate sample, consent, external voice id, delete/preview flow.

## Phase 3 — Voice Changer
- Add real adapter contract.
- RVC/OpenVoice adapters must be configured or blocked.
- Add similarity/naturalness/artifact QA.

## Phase 4 — SFX/BGM
- Add ElevenLabs SFX and Replicate/MusicGen style contracts.
- Persist license metadata.

## Phase 5 — Podcast
- Build full episode pipeline: speaker casting → TTS per segment → timeline → ducking → final export.

## Phase 6 — Audio QA
- Replace duplicate validators with `UnifiedAudioQAPipeline`.

## Phase 7 — Frontend
- Add capability-aware API and guard cards.
