# backend/app/api/audio.py

## 1) Imports
Add:
```python
from uuid import uuid4
from app.services.object_storage import upload_file_to_object_storage
from app.workers.narration_worker import run_narration_job_task
```

## 2) `post_voice_profile(...)`
Pass provider through:
```python
row = create_voice_profile(
    db,
    display_name=payload.display_name,
    provider=payload.provider,
    clone_mode=payload.clone_mode,
    ...
)
```

## 3) `post_voice_sample(...)`
Replace temporary filename creation:
```python
safe_name = Path(file.filename or "sample.bin").name
temp_path = Path(tmpdir) / safe_name
...
filename=safe_name,
```

## 4) `post_audio_preview(...)`
Replace the simple return with preview artifact handling:
```python
with tempfile.TemporaryDirectory() as tmpdir:
    preview_name = f"preview_{uuid4().hex}.mp3"
    preview_path = Path(tmpdir) / preview_name
    preview_path.write_bytes(audio_bytes)
    storage_key = f"audio/previews/{profile.id}/{preview_name}"
    public_url = None
    try:
        stored = upload_file_to_object_storage(
            local_path=str(preview_path),
            key=storage_key,
            content_type="audio/mpeg",
        )
        storage_key = stored.key
        public_url = stored.public_url
    except Exception:
        public_url = None

return {
    "ok": True,
    "bytes_length": len(audio_bytes),
    "preview_url": public_url,
    "preview_storage_key": storage_key,
    "voice_profile_id": profile.id,
    "provider": profile.provider,
    "content_type": "audio/mpeg",
}
```

## 5) `post_narration_job(...)`
Replace sync execution:
```python
run_narration_job_task.delay(row.id)
db.refresh(row)
return _narration_job_to_response(db, row)
```

## 6) `post_music_asset_upload(...)`
Sanitize filename:
```python
safe_name = Path(file.filename or "music.bin").name
temp_path = Path(tmpdir) / safe_name
...
filename=safe_name,
```
