import uuid

from app.models.audio_job import AudioJob
from app.models.voice import Voice


def test_audio_preview_route_persists_workflow_type_and_task_shape(client, db_session):
    response = client.post('/api/v1/audio/preview', json={'text': 'hello world', 'voice': 'default'})
    assert response.status_code == 201
    job_id = response.json()['job_id']

    job = db_session.query(AudioJob).filter(AudioJob.id == uuid.UUID(job_id)).one()
    assert job.workflow_type == 'tts_preview'
    assert job.request_json['text'] == 'hello world'
    assert job.request_json['voice'] == 'default'


def test_conversation_route_persists_task_request_shape(client, db_session):
    response = client.post(
        '/api/v1/conversation/generate',
        json={
            'script': [
                {'speaker': 'A', 'text': 'Hello'},
                {'speaker': 'B', 'text': 'Hi'},
            ],
            'speaker_voice_map': {'A': None, 'B': None},
            'provider_strategy': 'per_voice',
            'merge_output': True,
        },
    )
    assert response.status_code == 200
    job_id = response.json()['job_id']

    job = db_session.query(AudioJob).filter(AudioJob.id == uuid.UUID(job_id)).one()
    assert job.workflow_type == 'conversation'
    assert len(job.request_json['conversation_turns']) == 2
    assert job.request_json['conversation_turns'][0]['speaker'] == 'A'


def test_clone_preview_route_persists_task_request_shape(client, db_session):
    voice_uuid = uuid.UUID('00000000-0000-0000-0000-000000000123')
    existing = db_session.get(Voice, voice_uuid)
    if existing is None:
        db_session.add(Voice(id=voice_uuid, name='CI Voice'))
        db_session.commit()

    response = client.post(f'/api/v1/voice-clone/{voice_uuid}/preview', json={'text': 'preview me'})
    assert response.status_code == 200
    job_id = response.json()['job_id']

    job = db_session.query(AudioJob).filter(AudioJob.id == uuid.UUID(job_id)).one()
    assert job.workflow_type == 'clone_preview'
    assert job.request_json['text'] == 'preview me'
    assert job.request_json['voice_id'] == str(voice_uuid)
    assert job.request_json['clone_source_key'] == str(voice_uuid)


def test_tts_preview_idempotency_key_deduplicates_job(client, db_session):
    headers = {'Idempotency-Key': 'idem-tts-preview-001'}

    first = client.post('/api/v1/tts/preview', json={'text': 'hello dedupe'}, headers=headers)
    assert first.status_code == 200

    second = client.post('/api/v1/tts/preview', json={'text': 'hello dedupe'}, headers=headers)
    assert second.status_code == 200

    first_job_id = first.json()['job_id']
    second_job_id = second.json()['job_id']
    assert first_job_id == second_job_id
    assert first.json()['idempotency_key'] == 'idem-tts-preview-001'

    jobs = db_session.query(AudioJob).filter(AudioJob.idempotency_key == 'idem-tts-preview-001').all()
    assert len(jobs) == 1
