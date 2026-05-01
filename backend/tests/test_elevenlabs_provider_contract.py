from app.providers.elevenlabs.schemas import CloneVoiceRequest, TTSRequest, VoiceSettings


def test_voice_settings_payload_contract():
    payload = VoiceSettings().to_payload()
    assert set(payload) == {"stability", "similarity_boost", "style", "speed", "use_speaker_boost"}


def test_tts_request_defaults():
    req = TTSRequest(text="hello", voice_id="voice_123")
    assert req.model_id == "eleven_multilingual_v2"
    assert req.output_format.startswith("mp3")


def test_clone_requires_files_contract():
    req = CloneVoiceRequest(name="test", files=[("a.mp3", b"1234", "audio/mpeg")], consent_proof="manual")
    assert req.files[0][0] == "a.mp3"
    assert req.consent_proof == "manual"
