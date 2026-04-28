import secrets
import uuid
from uuid import UUID
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.affiliate import UserAffiliate, Referral, Commission, Payout
from app.schemas.affiliate import PayoutCreateRequest, UserAffiliateOut, PayoutOut


class AffiliateService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_affiliate(self, user_id: UUID, name: str, email: str) -> UserAffiliate:
        existing = self.db.query(UserAffiliate).filter(UserAffiliate.user_id == user_id).one_or_none()
        if existing:
            return existing

        referral_code = secrets.token_urlsafe(8).upper().replace('-', '').replace('_', '')[:12]
        affiliate = UserAffiliate(user_id=user_id, name=name, email=email, referral_code=referral_code)
        self.db.add(affiliate)
        self.db.commit()
        self.db.refresh(affiliate)
        return affiliate

    def get_affiliate(self, user_id: UUID) -> UserAffiliate | None:
        return self.db.query(UserAffiliate).filter(UserAffiliate.user_id == user_id).one_or_none()

    def get_referral_code(self, referral_code: str) -> UserAffiliate | None:
        return self.db.query(UserAffiliate).filter(UserAffiliate.referral_code == referral_code).one_or_none()

    def create_referral(self, affiliate_id: UUID, referred_email: str) -> Referral:
        existing = self.db.query(Referral).filter(
            Referral.affiliate_id == affiliate_id,
            Referral.referred_email == referred_email,
        ).one_or_none()
        if existing:
            return existing

        referral = Referral(affiliate_id=affiliate_id, referred_email=referred_email, status='pending')
        self.db.add(referral)
        self.db.commit()
        self.db.refresh(referral)
        return referral

    def list_referrals(self, affiliate_id: UUID) -> list[Referral]:
        return self.db.query(Referral).filter(Referral.affiliate_id == affiliate_id).order_by(Referral.created_at.desc()).all()

    def list_commissions(self, affiliate_id: UUID) -> list[Commission]:
        return self.db.query(Commission).filter(Commission.affiliate_id == affiliate_id).order_by(Commission.created_at.desc()).all()

    def get_total_earnings(self, affiliate_id: UUID) -> int:
        total = self.db.query(Commission).filter(Commission.affiliate_id == affiliate_id).with_entities(
            func.sum(Commission.amount_cents)
        ).scalar() or 0
        return int(total)

    def get_pending_balance(self, affiliate_id: UUID) -> int:
        paid = self.db.query(Payout).filter(
            Payout.affiliate_id == affiliate_id,
            Payout.status == 'completed',
        ).with_entities(func.sum(Payout.amount_cents)).scalar() or 0
        total = self.get_total_earnings(affiliate_id)
        return total - int(paid)

    def request_payout(self, affiliate_id: UUID, payload: PayoutCreateRequest) -> Payout:
        payout = Payout(
            affiliate_id=affiliate_id,
            amount_cents=payload.amount_cents,
            payout_method=payload.payout_method,
            payout_destination=payload.payout_destination,
            note=payload.note,
            status='pending',
        )
        self.db.add(payout)
        self.db.commit()
        self.db.refresh(payout)
        return payout

    def list_payouts(self, affiliate_id: UUID) -> list[Payout]:
        return self.db.query(Payout).filter(Payout.affiliate_id == affiliate_id).order_by(Payout.requested_at.desc()).all()
