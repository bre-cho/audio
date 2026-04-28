from pathlib import Path


def test_voice_clone_upload_stores_audio_sample(client, monkeypatch, tmp_path):
    monkeypatch.setenv('ARTIFACT_ROOT', str(tmp_path))

    response = client.post(
        '/api/v1/voice-clone/upload',
        files={'file': ('sample.wav', b'RIFFdemo-audio', 'audio/wav')},
    )

    assert response.status_code == 200
    body = response.json()
    stored_path = tmp_path / body['file_id']
    assert body['file_id'].startswith('voice-clone/samples/')
    assert body['upload_url'] == f"/artifacts/{body['file_id']}"
    assert stored_path.exists()
    assert stored_path.read_bytes() == b'RIFFdemo-audio'


def test_voice_clone_upload_rejects_non_audio_file(client):
    response = client.post(
        '/api/v1/voice-clone/upload',
        files={'file': ('notes.txt', b'not audio', 'text/plain')},
    )

    assert response.status_code == 400
    assert response.json()['detail'] == 'Chi ho tro tai len tep audio'