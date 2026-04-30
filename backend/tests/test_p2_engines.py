"""Tests for P2 engine implementations: noise reducer, voice enhancer, podcast mixer."""
from __future__ import annotations

import base64
import io
import math
import struct
import wave

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_wav(
    duration_ms: int = 800,
    framerate: int = 44100,
    nchannels: int = 1,
    sampwidth: int = 2,
    freq_hz: float = 440.0,
    amplitude: float = 0.5,
) -> bytes:
    """Generate a sine-wave WAV for testing."""
    n_frames = framerate * duration_ms // 1000
    max_val = 32767 if sampwidth == 2 else 127
    samples = [
        int(max_val * amplitude * math.sin(2 * math.pi * freq_hz * i / framerate))
        for i in range(n_frames * nchannels)
    ]
    if sampwidth == 1:
        raw = bytes(max(0, min(255, s + 128)) for s in samples)
    else:
        raw = struct.pack(f"<{len(samples)}h", *samples)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(nchannels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(raw)
    return buf.getvalue()


def _wav_duration_ms(data: bytes) -> int:
    with wave.open(io.BytesIO(data), "rb") as wf:
        return int(wf.getnframes() / wf.getframerate() * 1000)


# ---------------------------------------------------------------------------
# Noise Reducer Engine
# ---------------------------------------------------------------------------

class TestNoiseReducerEngine:
    def test_returns_valid_wav(self):
        from app.audio_engines.noise_reducer.noise_pipeline import reduce_noise_wav
        wav = _make_wav(duration_ms=1000)
        out, report = reduce_noise_wav(input_wav=wav, strength=0.65)
        # Output should be valid WAV
        with wave.open(io.BytesIO(out), "rb") as wf:
            assert wf.getnframes() > 0

    def test_report_keys(self):
        from app.audio_engines.noise_reducer.noise_pipeline import reduce_noise_wav
        wav = _make_wav(duration_ms=800)
        _, report = reduce_noise_wav(input_wav=wav, strength=0.5)
        for key in ("noise_floor_rms", "gate_threshold", "frames_attenuated", "total_frames", "strength_applied"):
            assert key in report, f"missing key: {key}"

    def test_strength_zero_preserves_signal(self):
        from app.audio_engines.noise_reducer.noise_pipeline import reduce_noise_wav
        wav = _make_wav(duration_ms=600)
        out, report = reduce_noise_wav(input_wav=wav, strength=0.0)
        assert report["frames_attenuated"] == 0

    def test_invalid_wav_raises(self):
        from app.audio_engines.noise_reducer.noise_pipeline import reduce_noise_wav
        with pytest.raises(Exception):
            reduce_noise_wav(input_wav=b"not-a-wav", strength=0.5)


# ---------------------------------------------------------------------------
# Voice Enhancer Engine
# ---------------------------------------------------------------------------

class TestVoiceEnhancerEngine:
    def test_clean_preset_returns_wav(self):
        from app.audio_engines.enhancer.enhancement_pipeline import enhance_voice_wav
        wav = _make_wav(duration_ms=800)
        out, report = enhance_voice_wav(input_wav=wav, preset="clean")
        with wave.open(io.BytesIO(out), "rb") as wf:
            assert wf.getnframes() > 0
        assert report["preset_resolved"] == "clean"
        assert "normalize" in report["stages_applied"]

    def test_broadcast_preset_applies_stages(self):
        from app.audio_engines.enhancer.enhancement_pipeline import enhance_voice_wav
        wav = _make_wav(duration_ms=800)
        _, report = enhance_voice_wav(input_wav=wav, preset="broadcast")
        assert "high_pass" in report["stages_applied"]
        assert "compress" in report["stages_applied"]

    def test_podcast_preset(self):
        from app.audio_engines.enhancer.enhancement_pipeline import enhance_voice_wav
        wav = _make_wav(duration_ms=800)
        _, report = enhance_voice_wav(input_wav=wav, preset="podcast")
        assert "compress" in report["stages_applied"]
        assert "dc_block" in report["stages_applied"]

    def test_unknown_preset_falls_back_to_clean(self):
        from app.audio_engines.enhancer.enhancement_pipeline import enhance_voice_wav
        wav = _make_wav(duration_ms=600)
        _, report = enhance_voice_wav(input_wav=wav, preset="nonexistent")
        assert report["preset_resolved"] == "clean"

    def test_output_peak_within_range(self):
        from app.audio_engines.enhancer.enhancement_pipeline import enhance_voice_wav
        wav = _make_wav(duration_ms=800, amplitude=0.1)  # quiet input
        _, report = enhance_voice_wav(input_wav=wav, preset="clean")
        # After normalize, peak should be close to 0.9 × 32767 ≈ 29490
        assert report["peak_out"] > 20000, "normalize should bring up quiet signal"


# ---------------------------------------------------------------------------
# Podcast Mixer Engine
# ---------------------------------------------------------------------------

class TestPodcastMixerEngine:
    def test_single_segment(self):
        from app.audio_engines.podcast.podcast_mixer import MixerSegment, mix_podcast_wav
        seg = MixerSegment(audio_wav=_make_wav(duration_ms=500), speaker="A")
        out, report = mix_podcast_wav(segments=[seg])
        assert report["segment_count"] == 1
        assert report["total_duration_ms"] >= 400

    def test_two_segments_concatenated(self):
        from app.audio_engines.podcast.podcast_mixer import MixerSegment, mix_podcast_wav
        s1 = MixerSegment(audio_wav=_make_wav(duration_ms=500, freq_hz=440), speaker="A", pause_after_ms=200)
        s2 = MixerSegment(audio_wav=_make_wav(duration_ms=500, freq_hz=880), speaker="B", pause_after_ms=0)
        out, report = mix_podcast_wav(segments=[s1, s2])
        # Total should be ~500 + 200 silence + ~500 with crossfade
        assert report["total_duration_ms"] >= 900

    def test_report_has_segment_details(self):
        from app.audio_engines.podcast.podcast_mixer import MixerSegment, mix_podcast_wav
        segs = [
            MixerSegment(audio_wav=_make_wav(500), speaker="Host", pause_after_ms=100),
            MixerSegment(audio_wav=_make_wav(300), speaker="Guest"),
        ]
        _, report = mix_podcast_wav(segments=segs)
        assert len(report["segments"]) == 2
        assert report["segments"][0]["speaker"] == "Host"

    def test_empty_segments_raises(self):
        from app.audio_engines.podcast.podcast_mixer import mix_podcast_wav
        with pytest.raises(ValueError, match="no segments"):
            mix_podcast_wav(segments=[])

    def test_stereo_output(self):
        from app.audio_engines.podcast.podcast_mixer import MixerSegment, mix_podcast_wav
        seg = MixerSegment(audio_wav=_make_wav(500), speaker="A")
        out, report = mix_podcast_wav(segments=[seg], target_rate=16000, target_channels=2)
        with wave.open(io.BytesIO(out), "rb") as wf:
            assert wf.getnchannels() == 2
            assert wf.getframerate() == 16000


# ---------------------------------------------------------------------------
# API endpoints — /noise-reducer/status, /voice-enhancer/status, /podcast/status
# ---------------------------------------------------------------------------

class TestEngineStatusEndpoints:
    def test_noise_reducer_status_active(self):
        resp = client.get("/api/v1/noise-reducer/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["feature_status"] == "active"


class TestP2SingleFileEndpoints:
    def test_noise_reducer_process_via_b64(self):
        wav = base64.b64encode(_make_wav(600, freq_hz=440)).decode()
        payload = {
            "audio_b64": wav,
            "strength": 0.7,
            "noise_profile_ms": 250,
            "voice_profile": "narration",
        }
        resp = client.post("/api/v1/noise-reducer/process", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["noise_report"]["voice_profile"] == "narration"

    def test_voice_enhancer_process_via_b64(self):
        wav = base64.b64encode(_make_wav(700, freq_hz=330)).decode()
        payload = {
            "audio_b64": wav,
            "preset": "broadcast",
            "voice_profile": "broadcast",
        }
        resp = client.post("/api/v1/voice-enhancer/process", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["enhancement_report"]["preset_resolved"] == "broadcast"
        assert data["enhancement_report"]["voice_profile_resolved"] == "broadcast"

    def test_voice_enhancer_status_active(self):
        resp = client.get("/api/v1/voice-enhancer/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["feature_status"] == "active"
        assert "presets" in data

    def test_podcast_status_active(self):
        resp = client.get("/api/v1/podcast/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["feature_status"] == "active"


# ---------------------------------------------------------------------------
# API endpoint — /podcast/mix (inline base64 path, no file system needed)
# ---------------------------------------------------------------------------

class TestPodcastMixEndpoint:
    def test_mix_two_segments_via_b64(self):
        wav1 = base64.b64encode(_make_wav(500, freq_hz=440)).decode()
        wav2 = base64.b64encode(_make_wav(400, freq_hz=880)).decode()
        payload = {
            "title": "Test Episode",
            "segments": [
                {"audio_b64": wav1, "speaker": "Host", "pause_after_ms": 200},
                {"audio_b64": wav2, "speaker": "Guest", "pause_after_ms": 0},
            ],
        }
        resp = client.post("/api/v1/podcast/mix", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["mix_report"]["segment_count"] == 2
        assert data["mix_report"]["total_duration_ms"] >= 700

    def test_mix_missing_audio_returns_400(self):
        payload = {
            "title": "Bad Episode",
            "segments": [{"speaker": "Nobody", "pause_after_ms": 0}],
        }
        resp = client.post("/api/v1/podcast/mix", json=payload)
        assert resp.status_code == 400

    def test_mix_invalid_b64_returns_400(self):
        payload = {
            "title": "Bad B64",
            "segments": [{"audio_b64": "!!!notbase64!!!", "speaker": "X"}],
        }
        resp = client.post("/api/v1/podcast/mix", json=payload)
        assert resp.status_code == 400
