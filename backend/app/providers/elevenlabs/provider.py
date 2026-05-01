from __future__ import annotations
from typing import Iterator
import json
import mimetypes
from .client import ElevenLabsClient
from .schemas import *
from .errors import ElevenLabsError, ElevenLabsValidationError

class ElevenLabsProvider:
    name = "elevenlabs"
    code = "elevenlabs"

    def __init__(self, client: ElevenLabsClient | None = None):
        self.client = client or ElevenLabsClient()

    def _assert_audio(self, audio: bytes, action: str) -> None:
        if not audio or len(audio) < 128:
            raise ElevenLabsValidationError(f"{action}_returned_empty_or_too_small_audio")

    def get_usage(self) -> dict:
        resp = self.client.request("GET", "/v1/user/subscription")
        return resp.json()

    def list_voices(self, filters: dict | None = None) -> list[dict]:
        del filters
        resp = self.client.request("GET", "/v1/voices")
        return resp.json().get("voices", [])

    def get_voice_settings(self, voice_id: str) -> dict:
        resp = self.client.request("GET", f"/v1/voices/{voice_id}/settings")
        return resp.json()

    def health_check(self) -> ProviderHealth:
        try:
            usage = self.get_usage()
            voices = self.list_voices()
            ok = bool(voices) or usage is not None
            return ProviderHealth(
                provider=self.name,
                status="ok" if ok else "degraded",
                message="subscription_and_voices_verified" if ok else "verified_but_no_voices",
                usage=usage,
                capabilities={
                    "tts": ok,
                    "streaming_tts": ok,
                    "voice_clone": ok,
                    "voice_changer": ok,
                    "stt": ok,
                    "sound_effects": ok,
                    "audio_isolation": ok,
                },
            )
        except Exception as exc:
            return ProviderHealth(
                provider=self.name,
                status="blocked",
                message=str(exc),
                capabilities={"tts": False, "streaming_tts": False, "voice_clone": False, "voice_changer": False, "stt": False, "sound_effects": False, "audio_isolation": False},
            )

    def text_to_speech(self, req: TTSRequest) -> AudioResult:
        payload = {
            "text": req.text,
            "model_id": req.model_id,
            "voice_settings": req.voice_settings.to_payload(),
        }
        resp = self.client.request(
            "POST",
            f"/v1/text-to-speech/{req.voice_id}",
            params={"output_format": req.output_format},
            json=payload,
            headers={"accept": "audio/mpeg", "content-type": "application/json"},
        )
        self._assert_audio(resp.content, "tts")
        return AudioResult(audio_bytes=resp.content, content_type=resp.headers.get("content-type", "audio/mpeg"), model_id=req.model_id)

    def stream_text_to_speech(self, req: TTSRequest) -> Iterator[bytes]:
        payload = {
            "text": req.text,
            "model_id": req.model_id,
            "voice_settings": req.voice_settings.to_payload(),
        }
        with self.client.stream(
            "POST",
            f"/v1/text-to-speech/{req.voice_id}/stream",
            params={"output_format": req.output_format},
            json=payload,
            headers={"accept": "audio/mpeg", "content-type": "application/json"},
        ) as resp:
            if resp.status_code >= 400:
                raise ElevenLabsError(resp.read().decode("utf-8", errors="ignore")[:1000])
            for chunk in resp.iter_bytes():
                if chunk:
                    yield chunk

    def speech_to_speech(self, req: SpeechToSpeechRequest) -> AudioResult:
        data = {
            "model_id": req.model_id,
            "voice_settings": json.dumps(req.voice_settings.to_payload()),
        }
        files = {"audio": (req.filename, req.audio_bytes, "audio/mpeg")}
        resp = self.client.request(
            "POST",
            f"/v1/speech-to-speech/{req.target_voice_id}",
            params={"output_format": req.output_format},
            data=data,
            files=files,
            headers={"accept": "audio/mpeg"},
        )
        self._assert_audio(resp.content, "speech_to_speech")
        return AudioResult(audio_bytes=resp.content, content_type=resp.headers.get("content-type", "audio/mpeg"), model_id=req.model_id)

    def speech_to_text(self, req: STTRequest) -> TranscriptResult:
        data = {"model_id": req.model_id, "diarize": str(req.diarize).lower()}
        if req.language_code:
            data["language_code"] = req.language_code
        files = {"file": (req.filename, req.audio_bytes, "audio/mpeg")}
        resp = self.client.request("POST", "/v1/speech-to-text", data=data, files=files)
        payload = resp.json()
        return TranscriptResult(
            text=payload.get("text", ""),
            segments=payload.get("words") or payload.get("segments") or [],
            language_code=payload.get("language_code"),
            metadata={"raw": payload},
        )

    def generate_sound_effect(self, text: str, duration_seconds: float | None = None, prompt_influence: float | None = None) -> AudioResult:
        payload = {"text": text}
        if duration_seconds is not None:
            payload["duration_seconds"] = duration_seconds
        if prompt_influence is not None:
            payload["prompt_influence"] = prompt_influence
        resp = self.client.request("POST", "/v1/sound-generation", json=payload, headers={"accept": "audio/mpeg"})
        self._assert_audio(resp.content, "sound_effect")
        return AudioResult(audio_bytes=resp.content, content_type=resp.headers.get("content-type", "audio/mpeg"), metadata={"prompt": text})

    def isolate_audio(self, audio_bytes: bytes, filename: str) -> AudioResult:
        files = {"audio": (filename, audio_bytes, "audio/mpeg")}
        resp = self.client.request("POST", "/v1/audio-isolation", files=files, headers={"accept": "audio/mpeg"})
        self._assert_audio(resp.content, "audio_isolation")
        return AudioResult(audio_bytes=resp.content, content_type=resp.headers.get("content-type", "audio/mpeg"))

    # Legacy compatibility shim for old BaseTTSProvider contract.
    def generate_speech(self, payload: dict) -> dict:
        text = str(payload.get("text") or "")
        voice_id = str(payload.get("voice_id") or "")
        model_id = str(payload.get("model_id") or "eleven_multilingual_v2")
        output_format = str(payload.get("output_format") or "mp3_44100_128")
        request = TTSRequest(text=text, voice_id=voice_id, model_id=model_id, output_format=output_format)
        result = self.text_to_speech(request)
        return {
            "status": "ok",
            "provider": self.code,
            "audio_bytes": result.audio_bytes,
            "mime_type": result.content_type,
            "metadata": result.metadata,
        }

    # Legacy compatibility shim for old BaseTTSProvider contract.
    def clone_voice_legacy(self, payload: dict) -> dict:
        name = str(payload.get("name") or "").strip()
        if not name:
            raise ValueError("clone voice requires non-empty name")
        sample_files = payload.get("sample_files") or []
        files: list[tuple[str, bytes, str]] = []
        for idx, sample in enumerate(sample_files):
            filename = sample.get("filename") or f"sample-{idx + 1}.wav"
            content = sample.get("content") or b""
            content_type = sample.get("content_type") or mimetypes.guess_type(filename)[0] or "audio/wav"
            if not isinstance(content, (bytes, bytearray)):
                continue
            files.append((filename, bytes(content), content_type))
        if not files:
            raise ValueError("clone voice requires at least one sample file")
        req = CloneVoiceRequest(
            name=name,
            files=files,
            description=payload.get("description"),
            labels=payload.get("labels") or {},
            remove_background_noise=bool(payload.get("remove_background_noise", True)),
            consent_proof=payload.get("consent_proof"),
        )
        result = self.clone_voice(req)
        return {
            "status": "ok",
            "provider": self.code,
            "voice_id": result.voice_id,
            "requires_verification": result.requires_verification,
            "raw": result.metadata.get("raw", {}),
        }

    def clone_voice(self, req_or_payload):
        if isinstance(req_or_payload, CloneVoiceRequest):
            return self._clone_voice_impl(req_or_payload)
        return self.clone_voice_legacy(req_or_payload)

    def _clone_voice_impl(self, req: CloneVoiceRequest) -> CloneVoiceResult:
        data = {
            "name": req.name,
            "remove_background_noise": str(req.remove_background_noise).lower(),
        }
        if req.description:
            data["description"] = req.description
        if req.labels:
            data["labels"] = json.dumps(req.labels)
        files = [("files", (filename, content, mime)) for filename, content, mime in req.files]
        resp = self.client.request("POST", "/v1/voices/add", data=data, files=files)
        payload = resp.json()
        return CloneVoiceResult(
            voice_id=payload["voice_id"],
            requires_verification=bool(payload.get("requires_verification", False)),
            metadata={"consent_proof": req.consent_proof, "raw": payload},
        )
