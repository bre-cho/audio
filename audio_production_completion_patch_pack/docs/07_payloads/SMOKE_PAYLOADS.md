# SMOKE PAYLOADS

## TTS smoke
```json
{
  "text": "Xin chào, đây là bài kiểm tra giọng nói thật.",
  "voice_id": "default",
  "provider": "elevenlabs",
  "format": "wav"
}
```

## Voice clone smoke
```json
{
  "name": "Test Voice Clone",
  "provider": "elevenlabs",
  "consent": {
    "has_consent": true,
    "consent_text": "I confirm I own or have permission to use this voice sample.",
    "source": "user_upload"
  },
  "preview_text": "Đây là bản xem trước giọng nói đã được xác minh."
}
```

## Noise reducer smoke
```json
{
  "input_artifact_id": "artifact_id_here",
  "mode": "voice_cleanup",
  "strength": 0.65,
  "target_lufs": -16
}
```

## Podcast smoke
```json
{
  "title": "AI Audio Factory Demo",
  "speakers": [
    {"id": "host", "voice_id": "voice_a"},
    {"id": "guest", "voice_id": "voice_b"}
  ],
  "segments": [
    {"speaker": "host", "text": "Chào mừng bạn đến với podcast."},
    {"speaker": "guest", "text": "Rất vui được tham gia chương trình."}
  ],
  "target_lufs": -16
}
```
