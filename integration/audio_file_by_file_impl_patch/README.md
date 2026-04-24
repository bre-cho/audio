# Audio file-by-file implementation patch

This pack contains implementation-focused patches for these existing files in the uploaded repo:

- `backend/app/api/audio.py`
- `backend/app/services/audio/voice_clone_service.py`
- `backend/app/services/audio/narration_service.py`

Goals:
- remove hardcoded `ElevenLabsAdapter()` usage from API/business layer where possible
- sanitize uploads and avoid file overwrite collisions
- switch narration job execution from sync request path to Celery worker
- replace invalid MP3 byte concatenation with ffmpeg concat workflow
- return a real preview artifact path/URL instead of only `bytes_length`

Notes:
- These patches assume the repo already has `app.core.celery_app`, `app.workers.narration_worker`, `app.services.object_storage`, and `settings.ffmpeg_binary`.
- The patches are intentionally narrow and avoid broader schema migrations.
- `Minimax` is not wired in here; these changes only make the current ElevenLabs path safer and easier to extend.
