# FINEVOICE-STYLE AUDIO STUDIO PATCH PACK

Mục tiêu: nâng repo `audio-main` từ audio job backend thành **AI Voice Studio OS** theo benchmark FineVoice-style: Voice Library, TTS, Voice Clone, Voice Design, Voice Changer, Sound Effects, BGM, Podcast Generator, Voice Enhancer, Noise Reducer, Voice Isolator, STT/Subtitle/Translation, Provider Gate, Audio QA, Artifact Contract.

## Nguyên tắc apply

- Additive patch first: ưu tiên thêm file mới, hạn chế sửa core cũ.
- Không cho mock/silent WAV chạy ở production.
- Mọi engine phải khai báo capability trước khi route cho phép chạy.
- Mọi artifact audio phải qua Quality Gate trước khi promoted.
- Frontend chỉ hiện action khi backend capability = `ready` hoặc `degraded_allowed`.

## Thứ tự patch

1. P0 Truthful Provider Gate
2. P0 Audio Quality Gate
3. P1 Provider Capability Registry
4. P1 Voice Library + Voice Design
5. P2 Clone Mode + RVC Upload
6. P3 Voice Changer Engine
7. P4 SFX + BGM Generator
8. P5 Podcast Generator
9. P6 STT + Subtitle + Translation
10. P7 Frontend Studio Dashboard
11. CI verification

## Kết quả kỳ vọng

- Không còn pass giả bằng audio im lặng.
- API có `/api/system/capabilities` để frontend biết module nào sẵn sàng.
- Có model/schema cho voice profile, recipe, clone job, podcast timeline, audio QA.
- Có scaffold service/route để dev nối provider thật: ElevenLabs, Minimax, FineVoice-compatible, RVC, Demucs/RNNoise/STT.
