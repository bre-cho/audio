from __future__ import annotations

import os


class VoiceTranslateService:
    """Translate voice audio to another language.

    Dispatches to the provider specified by ``VOICE_TRANSLATION_PROVIDER``.

    Supported providers:
    - ``elevenlabs`` — uses the ElevenLabs dubbing API (async, polling).
    """

    def translate(self, payload: dict) -> dict:
        provider = os.getenv("VOICE_TRANSLATION_PROVIDER", "disabled").strip().lower()
        if provider in {"", "disabled", "none"}:
            raise RuntimeError(
                "voice_translation_provider_disabled: set VOICE_TRANSLATION_PROVIDER=elevenlabs"
            )
        if provider == "elevenlabs":
            return self._translate_elevenlabs(payload)
        raise RuntimeError(f"unsupported_voice_translation_provider:{provider}")

    def _translate_elevenlabs(self, payload: dict) -> dict:
        """Submit a dubbing job via ElevenLabs and return job metadata.

        The ``source_artifact_id`` must be a local file path or a resolvable
        artifact key.  The caller is responsible for polling the dubbing job
        status using the returned ``dubbing_id``.
        """
        from pathlib import Path

        from app.providers.elevenlabs.client import ElevenLabsClient

        source_artifact_id = payload.get("source_artifact_id") or ""
        target_language = payload.get("target_language") or ""
        if not source_artifact_id or not target_language:
            raise ValueError("source_artifact_id and target_language are required")

        # Resolve artifact to a local file; callers may pass a direct path
        source_path = Path(source_artifact_id)
        if not source_path.exists() or source_path.stat().st_size == 0:
            raise FileNotFoundError(
                f"voice_translate_source_file_not_found: {source_artifact_id!r}. "
                "Resolve the artifact to a local path before calling translate()."
            )

        client = ElevenLabsClient()
        with source_path.open("rb") as fh:
            resp = client.request(
                "POST",
                "/v1/dubbing",
                data={
                    "target_lang": target_language,
                    "mode": "automatic",
                    "watermark": "false",
                },
                files={
                    "file": (source_path.name, fh, "audio/mpeg"),
                },
            )
        body = resp.json()
        return {
            "status": "submitted",
            "provider": "elevenlabs",
            "dubbing_id": body.get("dubbing_id"),
            "expected_duration_sec": body.get("expected_duration_sec"),
            "target_language": target_language,
        }

    def translate_transcript(self, transcript: dict, target_language: str) -> dict:
        """Translate a text transcript dict (legacy interface)."""
        text = transcript.get("text") or ""
        if not text:
            raise ValueError("transcript.text is required")
        provider = os.getenv("VOICE_TRANSLATION_PROVIDER", "disabled").strip().lower()
        if provider in {"", "disabled", "none"}:
            raise RuntimeError(
                "voice_translation_provider_disabled: set VOICE_TRANSLATION_PROVIDER"
            )
        raise RuntimeError(
            "translate_transcript requires a text-translation provider integration (e.g. OpenAI, DeepL). "
            "Set VOICE_TRANSLATION_PROVIDER and implement the chosen provider adapter."
        )
