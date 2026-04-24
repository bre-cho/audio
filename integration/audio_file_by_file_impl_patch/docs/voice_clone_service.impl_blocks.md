# backend/app/services/audio/voice_clone_service.py

## 1) Imports and constants
Add:
```python
from uuid import uuid4

ALLOWED_AUDIO_MIME_TYPES = {
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
    "audio/wave", "audio/mp4", "audio/webm", "audio/ogg",
}
MAX_VOICE_SAMPLE_BYTES = 25 * 1024 * 1024
```

## 2) `create_voice_profile(...)`
Change signature and profile creation:
```python
def create_voice_profile(..., provider: str = "elevenlabs", ...):
    profile = VoiceProfile(
        display_name=display_name,
        provider=provider,
        ...
    )
```

## 3) `save_voice_sample(...)`
Add validation, safe pathing, and duplicate detection:
```python
if mime_type and mime_type not in ALLOWED_AUDIO_MIME_TYPES:
    raise ValueError(...)
source = Path(source_path)
if source.stat().st_size > MAX_VOICE_SAMPLE_BYTES:
    raise ValueError(...)

safe_name = Path(filename).name
target_path = target_dir / voice_profile_id / f"{uuid4().hex}_{safe_name}"
target_path.parent.mkdir(parents=True, exist_ok=True)

sha256_hex = hashlib.sha256(raw_bytes).hexdigest()
duplicate = (
    db.query(VoiceSample)
    .filter(VoiceSample.voice_profile_id == voice_profile_id, VoiceSample.sha256_hex == sha256_hex)
    .order_by(VoiceSample.created_at.desc())
    .first()
)
if duplicate is not None:
    target_path.unlink(missing_ok=True)
    return duplicate
```

## 4) Storage key and filename
Use the stored randomized filename in object storage:
```python
storage_key = f"audio/voice-samples/{voice_profile_id}/{target_path.name}"
filename=safe_name,
```

## 5) `clone_voice_if_needed(...)`
Add simple lifecycle and provider guard:
```python
profile.consent_status = "processing"
db.commit()

if profile.provider != "elevenlabs":
    profile.consent_status = "failed"
    ...
    return profile

result = await adapter.create_ivc_voice(...)
if result.get("ok"):
    profile.provider_voice_id = result["body"].get("voice_id")
    profile.consent_status = "confirmed"
    ...
    return profile

profile.consent_status = "failed"
profile.consent_text = (profile.consent_text or "") + f"\n[clone-error] ..."
```
