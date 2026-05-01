from __future__ import annotations


def convert_voice(*, source_artifact_id: str, mode: str, target_voice_id: str | None = None) -> dict:
    """Dispatch voice conversion to the configured provider.

    This function is intentionally thin — callers should use
    :class:`~app.audio_engines.voice_changer.conversion_adapter_v2.VoiceConversionAdapterV2`
    directly for full path/output control.  Raises ``RuntimeError`` with a
    clear message when ``VOICE_CONVERSION_PROVIDER`` is not configured so
    failures are never silent.
    """
    import os
    provider = os.getenv("VOICE_CONVERSION_PROVIDER", "disabled").lower()
    if provider in {"", "disabled", "none"}:
        raise RuntimeError(
            "voice_conversion_provider_disabled: set VOICE_CONVERSION_PROVIDER "
            "(supported: elevenlabs, rvc, openvoice)"
        )
    raise RuntimeError(
        f"convert_voice() legacy stub: use VoiceConversionAdapterV2 directly. "
        f"Provider '{provider}' requires input/output paths — pass them via the adapter."
    )
