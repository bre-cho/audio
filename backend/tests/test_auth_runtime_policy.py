import uuid

import jwt

from app.core.config import settings


def _set_auth_defaults(monkeypatch):
    monkeypatch.setattr(settings, 'auth_enabled', True)
    monkeypatch.setattr(settings, 'api_auth_tokens', None)
    monkeypatch.setattr(settings, 'jwt_audience', None)
    monkeypatch.setattr(settings, 'jwt_issuer', None)


def test_reject_short_jwt_key_in_production(client, monkeypatch):
    _set_auth_defaults(monkeypatch)
    monkeypatch.setattr(settings, 'app_env', 'production')
    monkeypatch.setattr(settings, 'jwt_secret_key', 'short-key')
    monkeypatch.setattr(settings, 'jwt_algorithm', 'HS256')

    token = jwt.encode({'sub': str(uuid.uuid4())}, 'short-key', algorithm='HS256')
    response = client.post('/api/v1/affiliate/enroll', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 500
    assert 'at least 32 chars' in response.json()['detail']


def test_allow_jwt_scope_for_admin_like_endpoint(client, monkeypatch):
    _set_auth_defaults(monkeypatch)
    monkeypatch.setattr(settings, 'app_env', 'dev')
    long_secret = 'this-is-a-long-enough-test-secret-for-hs256'
    monkeypatch.setattr(settings, 'jwt_secret_key', long_secret)
    monkeypatch.setattr(settings, 'jwt_algorithm', 'HS256')

    token = jwt.encode(
        {
            'sub': str(uuid.uuid4()),
            'scopes': ['ai-effects.init-defaults'],
        },
        long_secret,
        algorithm='HS256',
    )
    response = client.post('/api/v1/ai-effects/init-defaults', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    assert response.json()['status'] == 'initialized'


def test_deny_when_scope_missing(client, monkeypatch):
    _set_auth_defaults(monkeypatch)
    monkeypatch.setattr(settings, 'app_env', 'dev')
    long_secret = 'this-is-a-long-enough-test-secret-for-hs256'
    monkeypatch.setattr(settings, 'jwt_secret_key', long_secret)
    monkeypatch.setattr(settings, 'jwt_algorithm', 'HS256')

    token = jwt.encode(
        {
            'sub': str(uuid.uuid4()),
            'scopes': ['affiliate:read'],
        },
        long_secret,
        algorithm='HS256',
    )
    response = client.post('/api/v1/ai-effects/init-defaults', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 403


def test_api_auth_tokens_support_user_scope_role_mapping(client, monkeypatch):
    monkeypatch.setattr(settings, 'auth_enabled', True)
    monkeypatch.setattr(settings, 'jwt_secret_key', None)
    user_id = uuid.uuid4()
    monkeypatch.setattr(settings, 'api_auth_tokens', f'tkn123:{user_id}:ai-effects.init-defaults|affiliate.read:admin')

    enroll = client.post('/api/v1/affiliate/enroll', headers={'Authorization': 'Bearer tkn123'})
    assert enroll.status_code == 200
    assert enroll.json()['user_id'] == str(user_id)

    init_fx = client.post('/api/v1/ai-effects/init-defaults', headers={'Authorization': 'Bearer tkn123'})
    assert init_fx.status_code == 200
