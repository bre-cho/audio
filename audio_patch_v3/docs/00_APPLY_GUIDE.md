# 00 — APPLY GUIDE

## Nguyên tắc merge

Áp dụng theo thứ tự P0 → P7. Không đảo thứ tự.

```txt
P0 Truth Completion
P1 Provider Unification
P2 TTS + Clone Hardening
P3 Voice Changer Engine Contract
P4 Enhancer / Noise Reducer QA Gate
P5 SFX / BGM Provider Gate
P6 Podcast Production Engine
P7 Frontend Studio + Tests
```

## Cách apply nhanh

Từ root repo `audio-main`:

```bash
rsync -av --dry-run ../audio_patch_v3/patches/backend/ backend/
rsync -av --dry-run ../audio_patch_v3/patches/frontend/ frontend/

cp -R ../audio_patch_v3/patches/backend/* backend/
cp -R ../audio_patch_v3/patches/frontend/* frontend/
cp -R ../audio_patch_v3/smoke_payloads .smoke_payloads_v3

bash backend/scripts/verify_audio_v3.sh
```

## Hard gates sau khi apply

```txt
1. Any disabled/unwired feature returns 409/501, never fake queued.
2. Any provider output must pass non-empty audio validation.
3. internal_genvoice/mock/stub/placeholder cannot run in production.
4. Only one provider registry is source of truth.
5. No duplicate ElevenLabs adapter should be used by new code.
```
