# EXACT PATCH NOTES — AUDIO PROVIDER ROUTER

## Ý tưởng chính
Repo hiện có `provider_router.py` cho video render nhưng audio chưa dùng contract đó. Patch này tạo **router song song cho audio**, tránh đụng video provider core.

## Vì sao không sửa thẳng `provider_router.py`
- `provider_router.py` đang typed theo `BaseVideoProviderAdapter`
- audio contract khác hẳn video: list voices, clone voice, synthesize, compose music
- merge cả 2 vào một file lúc này sẽ tăng xung đột và làm render core rủi ro hơn

## Điểm nối thật trong repo hiện tại
- `backend/app/api/audio.py` đang gọi `ElevenLabsAdapter()` trực tiếp
- `backend/app/services/audio/voice_clone_service.py` đang hardcode `provider="elevenlabs"`
- `backend/app/services/audio/narration_service.py` đang synthesize qua `ElevenLabsAdapter()`

## Sau patch
- audio layer gọi `resolve_audio_provider(...)`
- audio layer lấy adapter qua `get_audio_provider_adapter(...)`
- business service không còn phụ thuộc trực tiếp vào `ElevenLabsAdapter`
- thêm provider mới chỉ cần add 1 adapter file + 1 nhánh trong router

## Phần nào chưa hoàn tất trong pack
- `MinimaxAudioProvider` mới là skeleton
- chưa đụng billing / usage ledger / fallback policy nâng cao
- chưa đưa music generation sang queue riêng
