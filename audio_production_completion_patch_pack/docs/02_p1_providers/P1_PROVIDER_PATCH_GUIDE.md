# P1 PROVIDER PATCH GUIDE — REAL PROVIDER LAYER

## Mục tiêu
Chuẩn hóa provider capability, hoàn thiện ElevenLabs/Minimax hoặc block rõ ràng, tránh provider giả chạy nhầm.

## P1.1 — Provider Capability Registry

### File thêm mới
`backend/app/providers/capability_registry.py`

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ProviderCapability:
    provider: str
    tts: bool = False
    voice_clone: bool = False
    voice_conversion: bool = False
    voice_design: bool = False
    sound_effect: bool = False
    noise_reduction: bool = False
    voice_enhancement: bool = False
    podcast_mix: bool = False
    production_ready: bool = False

CAPABILITIES = {
    "elevenlabs": ProviderCapability(
        provider="elevenlabs",
        tts=True,
        voice_clone=True,
        voice_design=True,
        sound_effect=True,
        production_ready=True,
    ),
    "minimax": ProviderCapability(
        provider="minimax",
        tts=False,
        voice_clone=False,
        production_ready=False,
    ),
    "internal_genvoice": ProviderCapability(
        provider="internal_genvoice",
        tts=True,
        production_ready=False,
    ),
}

def require_capability(provider: str, capability: str):
    caps = CAPABILITIES.get(provider)
    if not caps:
        raise ValueError(f"Unknown provider: {provider}")
    if not getattr(caps, capability, False):
        raise ValueError(f"Provider '{provider}' does not support capability '{capability}'")
    return caps
```

## P1.2 — Provider API surface

Mở rộng `backend/app/providers/base.py` hoặc `services/audio/provider_base.py` thành contract chung:

```python
class AudioProviderBase:
    code: str

    def synthesize(self, text: str, voice_id: str, **kwargs) -> dict: ...
    def clone_voice(self, name: str, files: list[bytes], consent: dict, **kwargs) -> dict: ...
    def get_voice(self, external_voice_id: str) -> dict: ...
    def list_voices(self) -> list[dict]: ...
    def design_voice(self, prompt: str, **kwargs) -> dict: ...
    def generate_sfx(self, prompt: str, **kwargs) -> dict: ...
```

## P1.3 — ElevenLabs clone real flow

### File cần sửa
`backend/app/providers/elevenlabs.py`

Flow bắt buộc:
1. Validate API key.
2. Validate consent.
3. Upload sample files.
4. Nhận `voice_id` từ provider.
5. Lưu `external_voice_id` vào DB.
6. Generate preview bằng voice mới.
7. Validate audio signal.
8. Chỉ mark succeeded khi preview pass.

Pseudo:
```python
result = client.voices.add(name=name, files=files, description=...)
external_voice_id = result["voice_id"]
preview = client.text_to_speech.convert(voice_id=external_voice_id, text=preview_text)
return {
  "status": "succeeded",
  "provider": "elevenlabs",
  "external_voice_id": external_voice_id,
  "preview_audio_bytes": preview,
}
```

## P1.4 — Minimax policy

Nếu chưa implement thật:
- API `/providers` phải trả `status="disabled"`.
- Worker gọi Minimax phải fail sớm với lỗi rõ.
- Không trả `queued` giả.

Nếu implement:
- mapping endpoint TTS
- mapping voice clone nếu provider hỗ trợ
- error handling
- timeout/retry
- signal validation

## P1.5 — Provider fallback policy

File đề xuất: `backend/app/services/provider_fallback_policy.py`

Rule:
- Provider user chọn thật mà fail → job failed.
- Chỉ fallback khi `ALLOW_PROVIDER_FALLBACK=true` và fallback provider có cùng capability + production_ready.
- Không fallback từ `elevenlabs` sang `internal_genvoice` trong production.

## P1.6 — Acceptance checklist

- [ ] `/providers` trả đúng capability matrix.
- [ ] Gọi provider không support capability → 400/422 rõ ràng.
- [ ] ElevenLabs clone có `external_voice_id` thật.
- [ ] Clone preview có signal report.
- [ ] Minimax chưa implement thì disabled, không queued giả.
