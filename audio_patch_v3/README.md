# AUDIO PRODUCTION COMPLETION PATCH PACK V3

Target snapshot: `audio-main-3(1).zip`.

Mục tiêu: fix trực tiếp các điểm yếu còn lại trong repo audio hiện tại để tiến gần production FineVoice-style Audio Studio:

- Không còn `queued` giả ở route chưa có job/engine thật.
- Một provider layer duy nhất, không duplicate ElevenLabs/Minimax logic.
- TTS/Clone có validation, decode, cost/latency hook, clone lifecycle.
- Voice Changer không còn pitch-shift-only được coi là production.
- SFX/BGM có provider adapter contract và hard gate.
- Podcast có episode builder/mixdown contract.
- Frontend hiển thị capability thật, disabled reason, job/artifact state.
- Test chặn regression mock/stub/silent/queued giả.

Bắt đầu đọc: `docs/00_APPLY_GUIDE.md`.
