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

        # Resolve artifact to a local file within the artifacts root; callers
        # should pass a path already scoped to ARTIFACT_ROOT.
        artifacts_root = Path(os.getenv("ARTIFACT_ROOT", "/artifacts")).resolve()
        source_path = Path(source_artifact_id).resolve()
        if artifacts_root not in source_path.parents and source_path != artifacts_root:
            raise ValueError(
                f"voice_translate_source_outside_artifacts_root: {source_path.name}. "
                "Provide a path within ARTIFACT_ROOT."
            )
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
        """Translate a text transcript dict to another language.

        Dispatches to the provider specified by ``TRANSLATION_PROVIDER``
        (independent of ``VOICE_TRANSLATION_PROVIDER`` which handles audio dubbing).

        Supported providers:
        - ``openai`` — GPT-4o-mini for fast, high-quality translation.
        - ``deepl`` — DeepL API (requires DEEPL_API_KEY).
        """
        text = transcript.get("text") or ""
        if not text:
            raise ValueError("transcript.text is required")

        provider = (
            os.getenv("TRANSLATION_PROVIDER")
            or os.getenv("VOICE_TRANSLATION_PROVIDER")  # backward-compat alias
            or "disabled"
        ).strip().lower()
        if provider in {"", "disabled", "none"}:
            raise RuntimeError(
                "text_translation_provider_disabled: set TRANSLATION_PROVIDER=openai or deepl"
            )

        if provider == "openai":
            return self._translate_openai(text, target_language)

        if provider == "deepl":
            return self._translate_deepl(text, target_language)

        raise RuntimeError(
            f"unsupported_translation_provider:{provider} — "
            "supported values: openai, deepl"
        )

    def _translate_openai(self, text: str, target_language: str) -> dict:
        import openai  # type: ignore[import]
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("translation_openai_missing_OPENAI_API_KEY")
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_TRANSLATION_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a professional translator. Translate the user's text "
                        f"to {target_language}. Return only the translated text without "
                        "any explanation or formatting."
                    ),
                },
                {"role": "user", "content": text},
            ],
            temperature=0.2,
        )
        translated = response.choices[0].message.content or ""
        return {
            "status": "completed",
            "provider": "openai",
            "original_text": text,
            "translated_text": translated,
            "target_language": target_language,
            "model": response.model,
        }

    def _translate_deepl(self, text: str, target_language: str) -> dict:
        import httpx
        api_key = os.getenv("DEEPL_API_KEY")
        if not api_key:
            raise RuntimeError("translation_deepl_missing_DEEPL_API_KEY")
        base_url = os.getenv("DEEPL_API_URL", "https://api-free.deepl.com/v2")
        response = httpx.post(
            f"{base_url}/translate",
            headers={"Authorization": f"DeepL-Auth-Key {api_key}"},
            data={"text": text, "target_lang": target_language.upper()},
            timeout=30.0,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"deepl_translation_failed:{response.status_code}:{response.text[:300]}"
            )
        body = response.json()
        translated = body.get("translations", [{}])[0].get("text", "")
        return {
            "status": "completed",
            "provider": "deepl",
            "original_text": text,
            "translated_text": translated,
            "target_language": target_language,
            "detected_source_language": body.get("translations", [{}])[0].get("detected_source_language"),
        }
