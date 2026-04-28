from __future__ import annotations

import io
import math
import wave

from app.workers.audio_tasks import process_audio_effect_job, process_voice_shift_job


def _make_wav_bytes(duration_sec: float = 0.2, sample_rate: int = 16000, freq_hz: float = 440.0) -> bytes:
    n_samples = int(duration_sec * sample_rate)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        frames = bytearray()
        for i in range(n_samples):
            s = int(12000 * math.sin(2 * math.pi * freq_hz * i / sample_rate))
            frames.extend(int(s).to_bytes(2, byteorder='little', signed=True))
        w.writeframes(bytes(frames))
    return buf.getvalue()


def test_voice_shift_job_writes_real_artifact(client, monkeypatch):
    # Route upload + create voice_shift job
    wav_bytes = _make_wav_bytes()
    resp = client.post(
        '/api/v1/voice-clone/shift?pitch_semitones=4',
        files={'file': ('sample.wav', wav_bytes, 'audio/wav')},
    )
    assert resp.status_code == 200
    job_id = resp.json()['id']

    # Execute real task logic synchronously
    result = process_voice_shift_job.run(job_id)
    assert result['status'] == 'succeeded'
    assert result['output_url']
    assert result['provider'] == 'internal_shift'


def test_ai_effect_job_writes_real_artifact(client, monkeypatch):
    monkeypatch.setattr("app.repositories.credit_repo.CreditRepository.get_balance", lambda self, uid: 1000)
    wav_bytes = _make_wav_bytes(freq_hz=330.0)
    params = '{"delay_ms":250,"feedback_ratio":0.5}'
    resp = client.post(
        f'/api/v1/ai-effects/apply?effect_type=echo&parameters={params}',
        files={'file': ('dry.wav', wav_bytes, 'audio/wav')},
    )
    assert resp.status_code == 200
    job_id = resp.json()['id']

    # Execute real task logic synchronously
    result = process_audio_effect_job.run(job_id)
    assert result['status'] == 'succeeded'
    assert result['output_url']
    assert result['effect_type'] == 'echo'
