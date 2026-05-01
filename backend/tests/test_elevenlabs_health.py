from app.providers.elevenlabs.schemas import ProviderHealth


def test_health_schema_has_capabilities():
    h = ProviderHealth(provider="elevenlabs", status="ok", message="ok", capabilities={"tts": True})
    assert h.capabilities["tts"] is True
