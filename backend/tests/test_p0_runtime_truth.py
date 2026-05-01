import os
from app.core.production_truth import assert_runtime_truth


def test_placeholder_provider_blocked_in_strict_mode(monkeypatch):
    monkeypatch.setenv("PROVIDER_STRICT_MODE", "true")
    monkeypatch.setenv("ALLOW_PLACEHOLDER_AUDIO", "false")
    decision = assert_runtime_truth("internal_genvoice", "tts")
    assert decision.allowed is False
    assert decision.status == "blocked"


def test_real_provider_allowed(monkeypatch):
    monkeypatch.setenv("PROVIDER_STRICT_MODE", "true")
    decision = assert_runtime_truth("elevenlabs", "tts")
    assert decision.allowed is True
