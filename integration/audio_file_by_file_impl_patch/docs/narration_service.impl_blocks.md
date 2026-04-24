# backend/app/services/audio/narration_service.py

## 1) Imports
Add:
```python
import subprocess
```

## 2) Provider guard in `run_narration_job(...)`
Insert before adapter creation:
```python
if job.provider and job.provider != profile.provider:
    profile.provider = job.provider
    db.commit()
    db.refresh(profile)

if profile.provider != "elevenlabs":
    job.status = "failed"
    job.error_message = f"Unsupported narration provider: {profile.provider}"
    db.commit()
    return job
```

## 3) Replace byte concatenation state
Change:
```python
combined_audio = b""
```
to:
```python
segment_paths: list[Path] = []
```

## 4) Inside the segment loop
After `segment.output_local_path = ...` add:
```python
segment_paths.append(segment_path)
```

Remove:
```python
combined_audio += audio_bytes
```

Add optional silence generation:
```python
pause_after_ms = int(segment.pause_after_ms or 0)
if pause_after_ms > 0:
    silence_path = output_dir / f"segment_{segment.segment_index:03d}_pause.mp3"
    subprocess.run([...], check=True, capture_output=True)
    segment_paths.append(silence_path)
```

## 5) Final merge
Replace:
```python
final_path.write_bytes(combined_audio)
```
with:
```python
concat_file = output_dir / "concat.txt"
concat_file.write_text(
    "\n".join(f"file '{p.as_posix()}'" for p in segment_paths),
    encoding="utf-8",
)
subprocess.run([
    settings.ffmpeg_binary,
    "-y", "-f", "concat", "-safe", "0",
    "-i", str(concat_file),
    "-c:a", "libmp3lame",
    str(final_path),
], check=True, capture_output=True)
```
