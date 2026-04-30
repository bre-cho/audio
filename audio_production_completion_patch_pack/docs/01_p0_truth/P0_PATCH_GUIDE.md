# P0 PATCH GUIDE — TRUTHFUL RUNTIME + AUDIO VALIDATION

## Mục tiêu
Chặn pass giả, chặn silent WAV/placeholder lọt production, đảm bảo artifact promoted phải có audio signal thật.

## P0.1 — Runtime mode guard

### File thêm mới
`backend/app/core/runtime_guard.py`

### Nội dung đề xuất
```python
from app.core.config import settings

PLACEHOLDER_PROVIDERS = {"internal_genvoice", "mock", "stub", "placeholder"}

class RuntimeGuardError(RuntimeError):
    pass

def is_production_like() -> bool:
    env = getattr(settings, "ENV", "development").lower()
    strict = str(getattr(settings, "PROVIDER_STRICT_MODE", "false")).lower() == "true"
    return env in {"production", "prod", "staging"} or strict

def assert_real_provider(provider: str, feature: str) -> None:
    if is_production_like() and provider in PLACEHOLDER_PROVIDERS:
        raise RuntimeGuardError(
            f"Blocked placeholder provider '{provider}' for feature '{feature}' in production-like runtime"
        )
```

### Wire vào
- `backend/app/workers/audio_tasks.py`
- `backend/app/workers/clone_tasks.py`
- `backend/app/services/provider_router.py`
- `backend/app/services/audio_provider_router.py`

Rule:
```python
assert_real_provider(provider, feature="tts")
```

## P0.2 — Audio signal validation

### File thêm mới
`backend/app/services/audio_quality/audio_signal_validator.py`

```python
import io
import wave
import audioop
from dataclasses import dataclass

@dataclass
class AudioSignalReport:
    passed: bool
    duration_ms: int
    rms: int
    peak: int
    reason: str | None = None


def validate_wav_signal(data: bytes, min_duration_ms: int = 300, min_rms: int = 20) -> AudioSignalReport:
    try:
        with wave.open(io.BytesIO(data), "rb") as wav:
            frames = wav.readframes(wav.getnframes())
            rate = wav.getframerate()
            width = wav.getsampwidth()
            duration_ms = int((wav.getnframes() / rate) * 1000) if rate else 0
            rms = audioop.rms(frames, width) if frames else 0
            peak = audioop.max(frames, width) if frames else 0
    except Exception as exc:
        return AudioSignalReport(False, 0, 0, 0, f"invalid_wav:{exc}")

    if duration_ms < min_duration_ms:
        return AudioSignalReport(False, duration_ms, rms, peak, "duration_too_short")
    if rms < min_rms:
        return AudioSignalReport(False, duration_ms, rms, peak, "silent_or_near_silent")
    return AudioSignalReport(True, duration_ms, rms, peak, None)
```

## P0.3 — Artifact metadata extension

### DB migration cần thêm
Thêm field vào artifact/output model tương ứng:
- `generation_mode`: `real | placeholder | degraded`
- `provider_verified`: bool
- `audio_contains_signal`: bool
- `signal_rms`: int nullable
- `signal_peak`: int nullable
- `quality_report`: JSON nullable

Nếu chưa muốn migrate ngay, lưu tạm vào JSON metadata nhưng phải có migration ở P1.

## P0.4 — Disable silent WAV promotion

### File cần sửa
`backend/app/services/audio_artifact_service.py`

Rule:
- `_silent_wav_bytes()` chỉ được dùng khi `ENV=development` và `ALLOW_PLACEHOLDER_AUDIO=true`.
- Artifact silent phải có `generation_mode="placeholder"`.
- `promotion_status` không được là `contract_verified` nếu `audio_contains_signal=false`.

Pseudo patch:
```python
if generation_mode != "real":
    promotion_status = "blocked"
    promotion_reason = "placeholder audio cannot be promoted"
```

## P0.5 — Job success gate

### File cần sửa
`backend/app/audio_factory/job_finalizer.py`

Thêm check:
```python
if artifact.generation_mode != "real": block
if artifact.audio_contains_signal is not True: block
if artifact.provider_verified is not True: block
```

## P0.6 — Acceptance checklist

- [ ] Production mode không cho `internal_genvoice` chạy.
- [ ] Silent WAV không thể promoted.
- [ ] TTS job provider thật mà fail thì status = failed, không fallback im lặng.
- [ ] Artifact phải có checksum + signal report.
- [ ] CI có test tạo WAV im lặng và verify bị block.
