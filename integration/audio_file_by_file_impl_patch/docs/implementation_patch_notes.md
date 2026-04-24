# Implementation patch notes

## 1. `api/audio.py`

Key changes:
- sanitize uploaded filenames with `Path(...).name`
- use a temporary preview file and return `preview_url`, `preview_storage_key`, and `content_type`
- enqueue narration work through `run_narration_job_task.delay(...)` instead of awaiting the whole job in request scope

## 2. `services/audio/voice_clone_service.py`

Key changes:
- avoid overwriting files by placing samples in `voice_profile_id/uuid_filename`
- validate MIME type and sample size before copying
- compute sha256 before persistence and skip duplicate uploads for the same voice profile
- accept provider as input in `create_voice_profile(...)`
- set safer lifecycle transitions in `clone_voice_if_needed(...)`

## 3. `services/audio/narration_service.py`

Key changes:
- remove `combined_audio += audio_bytes`
- collect `segment_paths`, build an ffmpeg concat list, and render a final MP3 via ffmpeg
- add optional silence segments based on `pause_after_ms`
- keep object storage upload for both segment files and final output
- set `job.duration_ms` from segment estimates as a fallback; exact ffprobe duration can be added later

## Manual follow-ups after applying

- add Alembic migrations if you later extend model fields such as `clone_status`
- add a dedicated helper for exact audio duration using ffprobe if you want precise duration accounting
- move preview files to object storage-only signed URLs if local file serving is disabled in your environment
