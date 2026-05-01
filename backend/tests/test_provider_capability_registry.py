from app.services.provider_capability_registry import ProviderCapabilityRegistry


def test_missing_capability_is_blocked():
    reg = ProviderCapabilityRegistry()
    cap = reg.get('unknown', 'tts')
    assert cap.status == 'blocked'
    assert cap.reason == 'capability_not_registered'


def test_ready_capability_passes():
    reg = ProviderCapabilityRegistry()
    reg.register('elevenlabs', 'tts', 'ready')
    reg.assert_ready('elevenlabs', 'tts')
