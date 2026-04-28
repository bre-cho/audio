import uuid

import jwt
from app.core.config import settings
from app.models.affiliate import Commission
from app.schemas.affiliate import PayoutCreateRequest
from app.services.affiliate_service import AffiliateService


def _auth_header_for(user_id: uuid.UUID, monkeypatch) -> dict[str, str]:
    monkeypatch.setattr(settings, 'auth_enabled', True)
    monkeypatch.setattr(settings, 'jwt_secret_key', 'test-secret')
    monkeypatch.setattr(settings, 'jwt_algorithm', 'HS256')
    monkeypatch.setattr(settings, 'jwt_audience', None)
    monkeypatch.setattr(settings, 'jwt_issuer', None)

    token = jwt.encode({'sub': str(user_id)}, 'test-secret', algorithm='HS256')
    return {'Authorization': f'Bearer {token}'}


def test_affiliate_to_voice_shift_to_commission_flow(client, db_session, monkeypatch):
    user_id = uuid.uuid4()
    headers = _auth_header_for(user_id, monkeypatch)

    enroll = client.post('/api/v1/affiliate/enroll', headers=headers)
    assert enroll.status_code == 200
    affiliate = enroll.json()
    assert affiliate['user_id'] == str(user_id)

    shift = client.post(
        '/api/v1/voice-clone/shift',
        headers=headers,
        files={'file': ('sample.wav', b'RIFF....WAVEfmt ', 'audio/wav')},
        params={'pitch_semitones': 2},
    )
    assert shift.status_code == 200
    shift_job = shift.json()
    assert shift_job['job_type'] == 'voice_shift'

    referral = client.post('/api/v1/affiliate/referrals', headers=headers, params={'email': 'buyer@example.com'})
    assert referral.status_code == 200
    referral_json = referral.json()

    service = AffiliateService(db_session)
    commission = Commission(
        affiliate_id=uuid.UUID(affiliate['id']),
        referral_id=uuid.UUID(referral_json['id']),
        amount_cents=2500,
        commission_type='voice_shift_referral',
        source_job_id=uuid.UUID(shift_job['id']),
    )
    db_session.add(commission)
    db_session.commit()

    earnings = client.get('/api/v1/affiliate/earnings', headers=headers)
    assert earnings.status_code == 200
    earnings_json = earnings.json()
    assert earnings_json['total_earnings_usd'] == 25.0

    commissions = client.get('/api/v1/affiliate/commissions', headers=headers)
    assert commissions.status_code == 200
    commissions_json = commissions.json()
    assert len(commissions_json) >= 1
    assert any(item['commission_type'] == 'voice_shift_referral' for item in commissions_json)

    payout = client.post(
        '/api/v1/affiliate/payout',
        headers=headers,
        json=PayoutCreateRequest(
            amount_cents=2000,
            payout_method='bank_transfer',
            payout_destination='acct-test-001',
        ).model_dump(mode='json'),
    )
    assert payout.status_code == 200
    assert payout.json()['status'] == 'pending'
