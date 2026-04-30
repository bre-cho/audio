# AUDIO SMOKE PAYLOADS

## TTS
```json
{
  "text": "Xin chao, day la bai kiem tra giong noi that.",
  "voice_id": "default",
  "provider": "elevenlabs",
  "format": "wav"
}
```

## Voice clone
```json
{
  "name": "Test Voice Clone",
  "provider": "elevenlabs",
  "consent": {
    "has_consent": true,
    "consent_text": "I confirm I own or have permission to use this voice sample.",
    "source": "user_upload"
  },
  "preview_text": "Day la ban xem truoc giong noi da duoc xac minh."
}
```

## Podcast
```json
{
  "title": "AI Audio Factory Demo",
  "speakers": [
    {"id": "host", "voice_id": "voice_a"},
    {"id": "guest", "voice_id": "voice_b"}
  ],
  "segments": [
    {"speaker": "host", "text": "Chao mung ban den voi podcast."},
    {"speaker": "guest", "text": "Rat vui duoc tham gia chuong trinh."}
  ],
  "target_lufs": -16
}
```
