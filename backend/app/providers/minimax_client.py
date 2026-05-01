from __future__ import annotations

import base64
import binascii
import time
from pathlib import Path
from typing import Any

import httpx

from .minimax_errors import raise_for_http_status, raise_for_minimax_base_resp
from .minimax_models import (
    MinimaxAsyncTTSRequest,
    MinimaxAsyncTaskResult,
    MinimaxAsyncTaskStatus,
    MinimaxAudioResult,
    MinimaxCloneRequest,
    MinimaxCloneResult,
    MinimaxFileUploadResult,
    MinimaxTTSRequest,
    MinimaxVoiceDesignRequest,
    MinimaxVoiceDesignResult,
    ProviderHealth,
)


class MinimaxClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.minimax.io",
        group_id: str | None = None,
        timeout_seconds: float = 60.0,
        connect_timeout_seconds: float = 10.0,
    ) -> None:
        if not api_key:
            raise ValueError("MINIMAX_API_KEY is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.group_id = group_id
        self.timeout = httpx.Timeout(timeout_seconds, connect=connect_timeout_seconds)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(self._url(path), headers=self._headers(), json=payload)
        body = self._safe_json(response)
        raise_for_http_status(response.status_code, body)
        raise_for_minimax_base_resp(body)
        return body

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(self._url(path), headers=self._headers(), params=params)
        body = self._safe_json(response)
        raise_for_http_status(response.status_code, body)
        raise_for_minimax_base_resp(body)
        return body

    @staticmethod
    def _safe_json(response: httpx.Response) -> dict[str, Any]:
        try:
            data = response.json()
            return data if isinstance(data, dict) else {"data": data}
        except Exception:
            return {"raw_text": response.text[:1000]}

    @staticmethod
    def _decode_audio_hex_or_b64(value: str) -> bytes:
        if not value:
            return b""
        try:
            return bytes.fromhex(value)
        except ValueError:
            try:
                return base64.b64decode(value)
            except binascii.Error:
                return b""

    def health_check(self) -> ProviderHealth:
        started = time.perf_counter()
        try:
            raw = self.list_voices(voice_type="system")
            latency_ms = int((time.perf_counter() - started) * 1000)
            return ProviderHealth(provider="minimax", ok=True, status="ok", latency_ms=latency_ms, raw={"voice_count": len(raw.get("voices", []))})
        except Exception as exc:
            latency_ms = int((time.perf_counter() - started) * 1000)
            return ProviderHealth(provider="minimax", ok=False, status="error", reason=str(exc), latency_ms=latency_ms)

    def list_voices(self, *, voice_type: str = "all") -> dict[str, Any]:
        # Adjust path/query in integration if your Minimax account uses a region-specific endpoint.
        return self._post_json("/v1/get_voice", {"voice_type": voice_type})

    def synthesize_speech(self, request: MinimaxTTSRequest) -> MinimaxAudioResult:
        payload: dict[str, Any] = {
            "model": request.model,
            "text": request.text,
            "stream": False,
            "voice_setting": {
                "voice_id": request.voice_id,
                "speed": request.speed,
                "vol": request.volume,
                "pitch": request.pitch,
            },
            "audio_setting": {
                "audio_sample_rate": request.sample_rate or 32000,
                "bitrate": request.bitrate or 128000,
                "format": request.audio_format,
                "channel": 1,
            },
        }
        if request.language_boost:
            payload["language_boost"] = request.language_boost
        body = self._post_json("/v1/t2a_v2", payload)
        audio_value = ((body.get("data") or {}).get("audio") or body.get("audio") or "")
        audio_bytes = self._decode_audio_hex_or_b64(audio_value)
        if not audio_bytes:
            raise RuntimeError("Minimax TTS returned empty audio")
        return MinimaxAudioResult(
            audio_bytes=audio_bytes,
            audio_format=request.audio_format,
            provider="minimax",
            model=request.model,
            voice_id=request.voice_id,
            raw={"base_resp": body.get("base_resp"), "trace_id": body.get("trace_id")},
        )

    def create_async_tts_task(self, request: MinimaxAsyncTTSRequest) -> MinimaxAsyncTaskResult:
        payload = {
            "model": request.model,
            "text": request.text,
            "voice_id": request.voice_id,
            "output_format": request.audio_format,
        }
        body = self._post_json("/v1/t2a_async", payload)
        task_id = (body.get("data") or {}).get("task_id") or body.get("task_id")
        if not task_id:
            raise RuntimeError("Minimax async TTS did not return task_id")
        return MinimaxAsyncTaskResult(task_id=str(task_id), raw=body)

    def query_async_tts_task(self, task_id: str) -> MinimaxAsyncTaskStatus:
        body = self._get_json(f"/v1/t2a_async/{task_id}")
        data = body.get("data") or body
        return MinimaxAsyncTaskStatus(
            task_id=task_id,
            status=str(data.get("status") or data.get("task_status") or "unknown"),
            file_id=data.get("file_id"),
            download_url=data.get("download_url"),
            raw=body,
        )

    def upload_file(self, path: str | Path, *, purpose: str) -> MinimaxFileUploadResult:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(str(file_path))
        headers = {"Authorization": f"Bearer {self.api_key}"}
        with httpx.Client(timeout=self.timeout) as client:
            with file_path.open("rb") as fh:
                response = client.post(
                    self._url("/v1/files/upload"),
                    headers=headers,
                    data={"purpose": purpose},
                    files={"file": (file_path.name, fh, "application/octet-stream")},
                )
        body = self._safe_json(response)
        raise_for_http_status(response.status_code, body)
        raise_for_minimax_base_resp(body)
        file_id = ((body.get("file") or body.get("data") or {}).get("file_id") or body.get("file_id"))
        if not file_id:
            raise RuntimeError("Minimax upload did not return file_id")
        return MinimaxFileUploadResult(file_id=str(file_id), purpose=purpose, raw=body)

    def clone_voice(self, request: MinimaxCloneRequest) -> MinimaxCloneResult:
        payload: dict[str, Any] = {
            "file_id": request.clone_file_id,
            "voice_id": request.voice_id,
        }
        if request.clone_prompt:
            payload["clone_prompt"] = request.clone_prompt
        if request.prompt_file_id:
            payload["prompt_file_id"] = request.prompt_file_id
        body = self._post_json("/v1/voice_clone", payload)
        return MinimaxCloneResult(voice_id=request.voice_id, raw=body)

    def design_voice(self, request: MinimaxVoiceDesignRequest) -> MinimaxVoiceDesignResult:
        body = self._post_json("/v1/voice_design", {"prompt": request.prompt, "model": request.model})
        data = body.get("data") or body
        voice_id = data.get("voice_id")
        if not voice_id:
            raise RuntimeError("Minimax voice design did not return voice_id")
        trial = data.get("trial_audio")
        return MinimaxVoiceDesignResult(
            voice_id=str(voice_id),
            trial_audio_bytes=self._decode_audio_hex_or_b64(trial) if trial else None,
            raw=body,
        )

    def delete_voice(self, voice_id: str) -> dict[str, Any]:
        return self._post_json("/v1/delete_voice", {"voice_id": voice_id})
