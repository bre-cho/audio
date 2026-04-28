"""E2E tests for affiliate system."""
import pytest
import uuid
from sqlalchemy.orm import Session
from app.models.affiliate import Commission
from app.services.affiliate_service import AffiliateService


def _uid() -> uuid.UUID:
    return uuid.uuid4()


class TestAffiliateE2E:
    """End-to-end tests for affiliate system."""

    def test_01_enroll_affiliate(self, db_session: Session):
        """Test enrolling a user in the affiliate program."""
        user_id = _uid()
        service = AffiliateService(db_session)
        affiliate = service.get_or_create_affiliate(user_id=user_id, name="Test Affiliate", email="test@example.com")
        assert affiliate.user_id == user_id
        assert affiliate.referral_code is not None

    def test_02_create_referral(self, db_session: Session):
        """Test creating a referral."""
        user_id = _uid()
        service = AffiliateService(db_session)
        affiliate = service.get_or_create_affiliate(user_id=user_id, name="Test Aff", email="test@example.com")
        referral = service.create_referral(affiliate_id=affiliate.id, referred_email=f"customer-{uuid.uuid4().hex}@example.com")
        assert referral.affiliate_id == affiliate.id

    def test_03_commission_and_earnings(self, db_session: Session):
        """Test creating commissions and calculating earnings."""
        user_id = _uid()
        service = AffiliateService(db_session)
        affiliate = service.get_or_create_affiliate(user_id=user_id, name="Test Aff", email="test@example.com")
        for i in range(3):
            ref = service.create_referral(affiliate_id=affiliate.id, referred_email=f"customer-{uuid.uuid4().hex}-{i}@example.com")
            commission = Commission(affiliate_id=affiliate.id, referral_id=ref.id, amount_cents=5000, commission_type='signup')
            db_session.add(commission)
        db_session.commit()
        total = service.get_total_earnings(affiliate.id)
        assert total == 15000

    def test_04_payout_workflow(self, db_session: Session):
        """Test payout request workflow."""
        user_id = _uid()
        service = AffiliateService(db_session)
        affiliate = service.get_or_create_affiliate(user_id=user_id, name="Test Aff", email="test@example.com")
        ref = service.create_referral(affiliate_id=affiliate.id, referred_email=f"customer-{uuid.uuid4().hex}@example.com")
        commission = Commission(affiliate_id=affiliate.id, referral_id=ref.id, amount_cents=10000, commission_type='signup')
        db_session.add(commission)
        db_session.commit()
        from app.schemas.affiliate import PayoutCreateRequest
        payout = service.request_payout(affiliate_id=affiliate.id, payload=PayoutCreateRequest(amount_cents=5000, payout_method='bank_transfer', payout_destination='acct123'))
        assert payout.status == 'pending'
        pending = service.get_pending_balance(affiliate.id)
        assert pending == 10000
