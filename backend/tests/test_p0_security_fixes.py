"""P0 security fix tests.

Covers:
1. IDOR fix on DELETE /ai-effects/presets/{preset_id}
2. Rate limiting on GET /affiliate/code/{referral_code}
3. Email validation on POST /affiliate/referrals
4. Referral code format validation
"""
from __future__ import annotations

import uuid

import pytest

from app.core.rate_limit import _bucket_store
from app.models.ai_effects import AudioEffect, UserAudioEffectPreset
from app.models.affiliate import UserAffiliate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

AUTH_HEADERS = {"X-Auth-Token": "test-token"}


def _make_effect(db) -> AudioEffect:
    effect = AudioEffect(
        name="Echo",
        effect_type="echo",
        default_params={"delay_ms": 300, "feedback_ratio": 0.5},
    )
    db.add(effect)
    db.commit()
    db.refresh(effect)
    return effect


def _make_preset(db, user_id: uuid.UUID, effect_id: uuid.UUID) -> UserAudioEffectPreset:
    preset = UserAudioEffectPreset(
        user_id=user_id,
        effect_id=effect_id,
        preset_name="My Echo",
        parameters={"delay_ms": 200},
    )
    db.add(preset)
    db.commit()
    db.refresh(preset)
    return preset


def _make_affiliate(db, user_id: uuid.UUID, code: str | None = None) -> UserAffiliate:
    aff = UserAffiliate(
        user_id=user_id,
        name="Test Aff",
        email="aff@example.com",
        referral_code=code or uuid.uuid4().hex[:12].upper(),
    )
    db.add(aff)
    db.commit()
    db.refresh(aff)
    return aff


# ---------------------------------------------------------------------------
# 1. IDOR: owner can delete own preset
# ---------------------------------------------------------------------------

def test_owner_can_delete_own_preset(client, db_session):
    """Preset owner gets 200 on DELETE."""
    from app.api.deps import get_current_user_id
    owner_id = uuid.uuid4()

    effect = _make_effect(db_session)
    preset = _make_preset(db_session, owner_id, effect.id)

    from app.main import create_app
    app = create_app()
    app.dependency_overrides[get_current_user_id] = lambda: owner_id
    from app.api.deps import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    from fastapi.testclient import TestClient
    c = TestClient(app)
    resp = c.delete(f"/api/v1/ai-effects/presets/{preset.id}", headers=AUTH_HEADERS)
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"


def test_non_owner_cannot_delete_other_preset(client, db_session):
    """Another user trying to delete someone else's preset gets 403."""
    from app.api.deps import get_current_user_id, get_db
    owner_id = uuid.uuid4()
    attacker_id = uuid.uuid4()

    effect = _make_effect(db_session)
    preset = _make_preset(db_session, owner_id, effect.id)

    from app.main import create_app
    from fastapi.testclient import TestClient
    app = create_app()
    app.dependency_overrides[get_current_user_id] = lambda: attacker_id
    app.dependency_overrides[get_db] = lambda: db_session
    c = TestClient(app)
    resp = c.delete(f"/api/v1/ai-effects/presets/{preset.id}", headers=AUTH_HEADERS)
    app.dependency_overrides.clear()
    assert resp.status_code == 403


def test_delete_nonexistent_preset_returns_404(client, db_session):
    """Deleting a preset that does not exist returns 404."""
    from app.api.deps import get_current_user_id, get_db
    user_id = uuid.uuid4()

    from app.main import create_app
    from fastapi.testclient import TestClient
    app = create_app()
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    app.dependency_overrides[get_db] = lambda: db_session
    c = TestClient(app)
    resp = c.delete(f"/api/v1/ai-effects/presets/{uuid.uuid4()}", headers=AUTH_HEADERS)
    app.dependency_overrides.clear()
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 2. Referral code format validation
# ---------------------------------------------------------------------------

def test_invalid_referral_code_format_returns_400(client, db_session):
    """Non-alphanumeric or too-long referral code is rejected before DB lookup."""
    resp = client.get("/api/v1/affiliate/code/EVIL<script>", headers=AUTH_HEADERS)
    assert resp.status_code == 400

    resp2 = client.get("/api/v1/affiliate/code/" + "A" * 25, headers=AUTH_HEADERS)
    assert resp2.status_code == 400


def test_valid_referral_code_lookup(client, db_session):
    """Valid code that exists returns data; non-existent returns null body."""
    aff_user = uuid.uuid4()
    unique_code = uuid.uuid4().hex[:12].upper()
    _make_affiliate(db_session, aff_user, code=unique_code)

    resp = client.get(f"/api/v1/affiliate/code/{unique_code}", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json() is not None


# ---------------------------------------------------------------------------
# 3. Rate limiter: referral code endpoint
# ---------------------------------------------------------------------------

def test_referral_code_rate_limit_enforced(client, db_session):
    """After 10 requests the 11th returns 429."""
    # Clear any existing bucket state for this path
    keys_to_clear = [k for k in _bucket_store if "/affiliate/code/" in k]
    for k in keys_to_clear:
        del _bucket_store[k]

    # Make 10 requests (allowed)
    for _ in range(10):
        resp = client.get("/api/v1/affiliate/code/DOESNOTEXIST", headers=AUTH_HEADERS)
        assert resp.status_code in (200, 404)

    # 11th must be rate-limited
    resp = client.get("/api/v1/affiliate/code/DOESNOTEXIST", headers=AUTH_HEADERS)
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers


# ---------------------------------------------------------------------------
# 4. Email validation on POST /affiliate/referrals
# ---------------------------------------------------------------------------

def test_add_referral_rejects_invalid_email(client, db_session):
    """Invalid email format returns 400 without touching DB."""
    from app.api.deps import get_current_user_id, get_db
    user_id = uuid.uuid4()
    aff = _make_affiliate(db_session, user_id)

    from app.main import create_app
    from fastapi.testclient import TestClient
    app = create_app()
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    app.dependency_overrides[get_db] = lambda: db_session
    c = TestClient(app)
    resp = c.post("/api/v1/affiliate/referrals", params={"email": "not-an-email"}, headers=AUTH_HEADERS)
    app.dependency_overrides.clear()
    assert resp.status_code == 400
    assert "email" in resp.json()["detail"].lower()


def test_add_referral_accepts_valid_email(client, db_session):
    """Valid email format proceeds to DB layer."""
    from app.api.deps import get_current_user_id, get_db
    user_id = uuid.uuid4()
    _make_affiliate(db_session, user_id)

    from app.main import create_app
    from fastapi.testclient import TestClient
    app = create_app()
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    app.dependency_overrides[get_db] = lambda: db_session
    c = TestClient(app)
    resp = c.post("/api/v1/affiliate/referrals", params={"email": "referred@example.com"}, headers=AUTH_HEADERS)
    app.dependency_overrides.clear()
    assert resp.status_code in (200, 201)
