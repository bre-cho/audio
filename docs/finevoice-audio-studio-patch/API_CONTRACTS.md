# API CONTRACTS

## GET /api/system/capabilities

```json
{
  "environment": "production",
  "strict_mode": true,
  "modules": {
    "tts": {"status": "ready", "providers": ["elevenlabs"]},
    "voice_clone": {"status": "blocked", "reason": "provider_not_configured"},
    "voice_changer": {"status": "degraded", "reason": "pitch_shift_only"}
  }
}
```

## POST /api/voice-design/recipes

```json
{
  "name": "US Documentary Narrator",
  "language": "en-US",
  "gender": "neutral",
  "age": "adult",
  "style": "documentary",
  "emotion": "serious",
  "speed": 0.95,
  "pitch": -1,
  "provider": "elevenlabs"
}
```

## POST /api/sound-effects/generate

```json
{
  "prompt": "cinematic thunder impact",
  "duration_sec": 4,
  "style": "cinematic",
  "loopable": false
}
```

## POST /api/podcast/generate

```json
{
  "title": "AI News Brief",
  "script": "HOST: Welcome...\nGUEST: Thanks...",
  "speakers": [{"name": "HOST", "voice_id": "voice_1"}],
  "bgm": {"enabled": true, "ducking": true},
  "loudness_target_lufs": -16
}
```

## Audio QA result

```json
{
  "duration_sec": 13.4,
  "rms": 0.042,
  "peak": 0.81,
  "clipping_detected": false,
  "silence_detected": false,
  "loudness_lufs": -16.2,
  "qa_pass": true
}
```
