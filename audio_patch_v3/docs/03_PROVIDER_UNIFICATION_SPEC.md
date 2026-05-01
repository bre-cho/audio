# 03 — Provider Unification Spec

## Vấn đề hiện tại

Repo có nhiều adapter/provider song song:

```txt
app/providers/elevenlabs.py
app/providers/elevenlabs_real.py
app/services/audio/providers/elevenlabs_provider.py
app/providers/minimax.py
app/services/audio/providers/minimax_provider.py
```

## Luật mới

```txt
1 capability → 1 active provider → 1 adapter class.
No silent fallback.
No duplicate provider path for new code.
No mock/stub provider in staging/prod.
```

## Env chuẩn

```bash
TTS_PROVIDER=elevenlabs
VOICE_CLONE_PROVIDER=elevenlabs
VOICE_CONVERSION_PROVIDER=disabled
STT_PROVIDER=whisper
SFX_PROVIDER=disabled
BGM_PROVIDER=disabled
PODCAST_PROVIDER=local_mixdown
ELEVENLABS_API_KEY=...
PROVIDER_STRICT_MODE=true
ALLOW_PROVIDER_FALLBACK=false
ALLOW_PLACEHOLDER_AUDIO=false
```
