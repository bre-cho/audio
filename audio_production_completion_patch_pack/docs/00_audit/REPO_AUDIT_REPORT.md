# REPO AUDIT REPORT — audio-main(8)

## 1. Nhận định tổng quan
Repo đã có nền tảng backend khá đầy đủ cho một AI Audio Factory: FastAPI, Celery worker, SQLAlchemy models, artifact contract, storage local/S3, provider router, CI workflows và frontend cơ bản.

Tuy nhiên repo chưa thể gọi là production cho AI Voice Cloning / Voice Changer / Enhancer / Noise Reducer vì nhiều phần lõi vẫn là placeholder hoặc DSP đơn giản.

## 2. Module map hiện có

| Nhóm | File chính | Nhận xét |
|---|---|---|
| API Router | `backend/app/api/router.py` | Đã gom nhiều route |
| TTS | `backend/app/api/tts.py`, `services/tts_service.py`, `workers/audio_tasks.py` | Có job flow, cần provider thật + validation |
| Voice Clone | `api/voice_clone.py`, `services/voice_clone_service.py`, `workers/clone_tasks.py` | Có consent gate nhưng clone thật chưa đủ |
| AI Effects | `api/ai_effects.py`, `services/ai_effects_service.py` | Echo/EQ/Reverb đơn giản, chưa có SFX model |
| Conversation/Podcast | `api/conversation.py`, `services/conversation_service.py` | Có seed, thiếu multi-speaker mixer |
| Artifact Contract | `audio_factory/*`, `services/audio_artifact_service.py` | Khá mạnh nhưng đang cho placeholder pass quá dễ |
| Provider | `providers/elevenlabs.py`, `providers/minimax.py`, `services/provider_router.py` | ElevenLabs TTS có API, clone queued; Minimax chưa thật |
| Storage | `core/storage.py`, `services/object_storage.py` | Có local/S3 pattern |
| DB Models | `models/*.py` | Có job, voice, provider, artifact/output |
| Workers | `workers/audio_tasks.py`, `workers/clone_tasks.py` | Có Celery, cần queue taxonomy + DLQ |
| Frontend | `frontend/src/*` | Có UI cơ bản, cần map feature readiness |

## 3. Mock / placeholder / rủi ro production

### 3.1 Silent WAV fallback
File: `backend/app/services/audio_artifact_service.py`
- `DEFAULT_PROVIDER = "internal_genvoice"`
- `DEFAULT_TEMPLATE_VERSION = "audio-placeholder-v1"`
- `DEFAULT_MODEL_VERSION = "internal_genvoice/silent-wav-v1"`
- `_silent_wav_bytes()` tạo WAV im lặng.

Rủi ro: CI/artifact có thể pass dù không có audio thật.

### 3.2 Provider placeholder
File: `backend/app/api/providers.py`
- `internal_genvoice` status placeholder.

File: `backend/app/providers/minimax.py`
- trả `queued`, chưa implement thật.

File: `backend/app/services/audio/providers/minimax_provider.py`
- `NotImplementedError`.

### 3.3 ElevenLabs clone chưa đủ production
File: `backend/app/providers/elevenlabs.py`
- `clone_voice()` trả queued, chưa chứng minh upload sample/poll/save external voice id.

### 3.4 Voice changer chưa phải voice conversion thật
File: `backend/app/services/voice_clone_service.py` và worker tương ứng.
- Có pitch shift/resample, chưa có timbre transfer/formant preservation.

### 3.5 Enhancer / Noise reducer thiếu engine thật
Chưa thấy module DSP production gồm:
- RNNoise/WebRTC VAD
- spectral gate
- Demucs source separation
- de-click/de-ess/compressor/loudness normalize
- SNR/LUFS/clipping validation

### 3.6 Podcast generator thiếu mix engine
Thiếu:
- multi-speaker cast registry
- scene/chapter timeline
- intro/outro/stinger
- BGM ducking
- loudness target
- transcript alignment

## 4. Production gap matrix

| Feature | API | Worker | Provider thật | DB | Artifact QA | Status |
|---|---:|---:|---:|---:|---:|---|
| TTS | Có | Có | Một phần | Có | Một phần | Partial |
| Voice Clone | Có | Có | Thiếu | Có | Một phần | Not production |
| Voice Changer | Một phần | Có | Thiếu | Một phần | Thiếu | Not production |
| Voice Design | Thiếu sâu | Thiếu | Thiếu | Thiếu | Thiếu | Planned |
| SFX | Một phần effect | Một phần | Thiếu | Một phần | Thiếu | Planned |
| Podcast | Một phần | Một phần | Dùng TTS | Một phần | Thiếu | Partial |
| Enhancer | Thiếu | Thiếu | Nội bộ DSP | Thiếu | Thiếu | Planned |
| Noise Reducer | Thiếu | Thiếu | Nội bộ DSP | Thiếu | Thiếu | Planned |

## 5. Kết luận audit
Repo hiện là khung tốt. Việc cần làm không phải rewrite, mà là patch additive theo 3 lớp:

- P0: Truth runtime guard + audio validation + disable placeholder production.
- P1: Provider capability registry + real provider integration.
- P2: Engine thật cho voice design, changer, enhancer, noise reducer, SFX, podcast.
