from __future__ import annotations

from app.core.config import settings


def test_provider_callback_updates_job_status(client, monkeypatch):
    # Create a job first
    create_resp = client.post('/api/v1/audio/preview', json={'text': 'hello callback', 'voice': 'bella'})
    assert create_resp.status_code in (200, 201)
    job_id = create_resp.json()['id']

    monkeypatch.setattr(settings, 'provider_callback_token', 'secret-token', raising=False)

    cb_resp = client.post(
        '/api/v1/providers/callback/elevenlabs',
        headers={'X-Provider-Callback-Token': 'secret-token'},
        json={
            'job_id': job_id,
            'status': 'done',
            'output_url': '/artifacts/audio/from-provider.mp3',
            'provider_payload': {'request_id': 'abc-123'},
        },
    )
    assert cb_resp.status_code == 200
    assert cb_resp.json()['job_status'] == 'done'

    detail = client.get(f'/api/v1/jobs/{job_id}')
    assert detail.status_code == 200
    data = detail.json()
    assert data['status'] in ('done', 'success', 'succeeded')
    assert data['output_url'] == '/artifacts/audio/from-provider.mp3'


def test_provider_callback_rejects_invalid_token(client, monkeypatch):
    create_resp = client.post('/api/v1/audio/preview', json={'text': 'token check', 'voice': 'bella'})
    assert create_resp.status_code in (200, 201)
    job_id = create_resp.json()['id']

    monkeypatch.setattr(settings, 'provider_callback_token', 'expected-token', raising=False)

    cb_resp = client.post(
        '/api/v1/providers/callback/elevenlabs',
        headers={'X-Provider-Callback-Token': 'wrong-token'},
        json={'job_id': job_id, 'status': 'done'},
    )
    assert cb_resp.status_code == 401
