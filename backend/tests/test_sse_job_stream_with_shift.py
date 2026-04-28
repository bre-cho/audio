from __future__ import annotations

import io
import math
import os
import wave

import pytest


def _make_wav_bytes(duration_sec: float = 0.15, sample_rate: int = 16000, freq_hz: float = 220.0) -> bytes:
    n_samples = int(duration_sec * sample_rate)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        frames = bytearray()
        for i in range(n_samples):
            s = int(9000 * math.sin(2 * math.pi * freq_hz * i / sample_rate))
            frames.extend(int(s).to_bytes(2, byteorder='little', signed=True))
        w.writeframes(bytes(frames))
    return buf.getvalue()


def test_sse_stream_emits_voice_shift_job_updates(client):
    if os.getenv('RUN_SSE_LIVE_TEST') != '1':
        pytest.skip('Set RUN_SSE_LIVE_TEST=1 to run streaming integration test')
    # Submit a real voice-shift job; enqueue helper will execute via Celery or inline fallback.
    wav_bytes = _make_wav_bytes()
    created = client.post(
        '/api/v1/voice-clone/shift?pitch_semitones=2',
        files={'file': ('input.wav', wav_bytes, 'audio/wav')},
    )
    assert created.status_code == 200
    job_id = created.json()['id']

    # Read SSE stream and ensure payload includes the created job.
    with client.stream('GET', '/api/v1/jobs/stream') as resp:
        assert resp.status_code == 200
        chunks = []
        for text in resp.iter_text():
            chunks.append(text)
            joined = ''.join(chunks)
            if job_id in joined and 'voice_shift' in joined:
                assert 'event: jobs' in joined
                break
            if len(joined) > 12000:
                break

        assert job_id in ''.join(chunks)
