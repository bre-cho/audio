from __future__ import annotations


def test_providers_endpoint_returns_capability_matrix(client):
    response = client.get('/api/v1/providers')
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)

    by_code = {item['code']: item for item in body}
    assert by_code['elevenlabs']['production_ready'] is True
    assert by_code['minimax']['status'] == 'disabled'
    assert by_code['internal_genvoice']['status'] == 'placeholder'


def test_audio_capabilities_endpoint_truthful_readiness(client):
    response = client.get('/api/v1/audio/capabilities')
    assert response.status_code == 200
    payload = response.json()
    assert 'features' in payload

    features = {item['feature']: item for item in payload['features']}
    assert features['text_to_speech']['status'] in {'ready', 'partial', 'disabled'}
    assert features['noise_reducer']['status'] == 'ready'
    assert features['voice_enhancer']['status'] == 'ready'
    assert features['podcast_generator']['status'] == 'ready'
