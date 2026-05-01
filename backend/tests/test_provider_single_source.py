from app.providers.unified_provider_registry import SUPPORTED_BINDINGS, resolve_provider


def test_tts_elevenlabs_binding_exists():
    assert ("tts", "elevenlabs") in SUPPORTED_BINDINGS


def test_unknown_provider_rejected():
    try:
        resolve_provider("tts", "mock")
    except RuntimeError as exc:
        assert "provider_binding_not_supported" in str(exc)
    else:
        raise AssertionError("mock provider should not resolve")
