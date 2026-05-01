# AUDIO PRODUCTION COMPLETION PATCH PACK V4

Target repo: `audio-main-4(1).zip`

V4 closes the remaining production gaps found in the audit:

1. Canonical API routes: v2 routes become production routes; v1 routes must redirect/deprecate, never fake-queue.
2. Provider single source of truth: one registry, one adapter per provider, one capability gate.
3. Real-engine enforcement: Voice Changer, SFX, BGM, Podcast cannot return queued unless a real job is created.
4. Unified Audio QA pipeline: all generated audio passes the same validation path.
5. Frontend studio sync: UI disables blocked tools and explains why.
6. Test guards: no fake queued, no duplicate provider behavior, no placeholder artifacts.

Apply order:

```txt
P0_API_CANONICAL_ROUTE_PATCH
P1_PROVIDER_SINGLE_SOURCE_PATCH
P2_TTS_CLONE_LIFECYCLE_FINALIZATION
P3_VOICE_CHANGER_REAL_ADAPTER_PATCH
P4_SFX_BGM_REAL_PROVIDER_PATCH
P5_PODCAST_FULL_PRODUCTION_PATCH
P6_UNIFIED_AUDIO_QA_PIPELINE_PATCH
P7_FRONTEND_STUDIO_FINAL_SYNC_PATCH
```

Use this pack as additive scaffold. Do not delete existing files until tests pass. Existing v1 files should become compatibility wrappers.
