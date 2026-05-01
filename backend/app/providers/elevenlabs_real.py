from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


@dataclass(frozen=True)
class ProviderAudioResult:
    provider: str
    external_id: str | None
    audio_bytes: bytes | None
    metadata: dict[str, Any]


class ElevenLabsRealProvider:
    """Thin production adapter. Keep API-key handling outside logs."""

    base_url = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: str | None = None, timeout_sec: int | None = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise RuntimeError("missing_elevenlabs_api_key")
        self.timeout_sec = timeout_sec or int(os.getenv("ELEVENLABS_TIMEOUT_SEC", "90"))

    @property
    def headers(self) -> dict[str, str]:
        return {"xi-api-key": self.api_key}

    def text_to_speech(self, *, text: str, voice_id: str, model_id: str = "eleven_multilingual_v2") -> ProviderAudioResult:
        if not text.strip():
            raise ValueError("text_required")
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        payload = {"text": text, "model_id": model_id}
        with httpx.Client(timeout=self.timeout_sec) as client:
            resp = client.post(url, headers={**self.headers, "accept": "audio/mpeg"}, json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(f"elevenlabs_tts_failed:{resp.status_code}:{resp.text[:500]}")
        return ProviderAudioResult("elevenlabs", None, resp.content, {"voice_id": voice_id, "model_id": model_id})

    def clone_voice(self, *, name: str, sample_paths: list[str], description: str | None = None) -> ProviderAudioResult:
        if not sample_paths:
            raise ValueError("sample_paths_required")
        files = []
        handles = []
        try:
            for sample in sample_paths:
                p = Path(sample)
                if not p.exists() or p.stat().st_size == 0:
                    raise ValueError(f"invalid_sample:{sample}")
                h = open(p, "rb")
                handles.append(h)
                files.append(("files", (p.name, h, "audio/wav")))
            data = {"name": name, "description": description or ""}
            with httpx.Client(timeout=self.timeout_sec) as client:
                resp = client.post(f"{self.base_url}/voices/add", headers=self.headers, data=data, files=files)
            if resp.status_code >= 400:
                raise RuntimeError(f"elevenlabs_clone_failed:{resp.status_code}:{resp.text[:500]}")
            body = resp.json()
            voice_id = body.get("voice_id") or body.get("voice", {}).get("voice_id")
            if not voice_id:
                raise RuntimeError("elevenlabs_clone_missing_voice_id")
            return ProviderAudioResult("elevenlabs", voice_id, None, body)
        finally:
            for h in handles:
                h.close()
