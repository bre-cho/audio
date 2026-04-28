import re
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.api.deps import get_current_user_id, get_db
from app.core.rate_limit import rate_limit
from app.schemas.affiliate import UserAffiliateOut, PayoutCreateRequest, PayoutOut, ReferralOut, CommissionOut
from app.services.affiliate_service import AffiliateService

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

router = APIRouter()


@router.get('/me', response_model=UserAffiliateOut)
def get_current_affiliate(
    db: Session = Depends(get_db),
    user_id=Depends(get_current_user_id),
) -> UserAffiliateOut:
    """Get current user's affiliate profile if enrolled."""
    affiliate = AffiliateService(db).get_affiliate(user_id)
    if not affiliate:
        raise HTTPException(status_code=404, detail='Khong co affiliate profile')
    return UserAffiliateOut.model_validate(affiliate)


@router.post('/enroll', response_model=UserAffiliateOut)
def enroll_affiliate(
    request: Request,
    db: Session = Depends(get_db),
    user_id=Depends(get_current_user_id),
    _rl: None = Depends(rate_limit(5, 60)),
) -> UserAffiliateOut:
    """Enroll current user as affiliate."""
    service = AffiliateService(db)
    existing = service.get_affiliate(user_id)
    if existing:
        return UserAffiliateOut.model_validate(existing)
    
    affiliate = service.get_or_create_affiliate(user_id, 'Affiliate User', 'affiliate@example.com')
    return UserAffiliateOut.model_validate(affiliate)


@router.get('/code/{referral_code}', response_model=UserAffiliateOut | None)
def lookup_referral_code(
    referral_code: str,
    request: Request,
    db: Session = Depends(get_db),
    _rl: None = Depends(rate_limit(10, 60)),
) -> UserAffiliateOut | None:
    """Look up an affiliate by referral code (rate-limited: 10/min per IP)."""
    if not referral_code.isalnum() or len(referral_code) > 20:
        raise HTTPException(status_code=400, detail='Invalid referral code format')
    service = AffiliateService(db)
    affiliate = service.get_referral_code(referral_code)
    return UserAffiliateOut.model_validate(affiliate) if affiliate else None


@router.get('/referrals', response_model=list[ReferralOut])
def list_referrals(
    db: Session = Depends(get_db),
    user_id=Depends(get_current_user_id),
) -> list[ReferralOut]:
    """List all referrals for current user's affiliate account."""
    service = AffiliateService(db)
    affiliate = service.get_affiliate(user_id)
    if not affiliate:
        raise HTTPException(status_code=404, detail='Khong co affiliate profile')
    return [ReferralOut.model_validate(r) for r in service.list_referrals(affiliate.id)]


@router.post('/referrals', response_model=ReferralOut)
def add_referral(
    email: str,
    db: Session = Depends(get_db),
    user_id=Depends(get_current_user_id),
) -> ReferralOut:
    """Track a referral for current affiliate."""
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail='Invalid email address')
    service = AffiliateService(db)
    affiliate = service.get_affiliate(user_id)
    if not affiliate:
        raise HTTPException(status_code=404, detail='Khong co affiliate profile')
    referral = service.create_referral(affiliate.id, email)
    return ReferralOut.model_validate(referral)


@router.get('/earnings', response_model=dict)
def get_earnings(
    db: Session = Depends(get_db),
    user_id=Depends(get_current_user_id),
) -> dict:
    """Get total earnings and pending balance."""
    service = AffiliateService(db)
    affiliate = service.get_affiliate(user_id)
    if not affiliate:
        raise HTTPException(status_code=404, detail='Khong co affiliate profile')
    
    total_cents = service.get_total_earnings(affiliate.id)
    pending_cents = service.get_pending_balance(affiliate.id)
    
    return {
        'total_earnings_usd': total_cents / 100.0,
        'pending_balance_usd': pending_cents / 100.0,
        'currency': 'USD',
    }


@router.get('/commissions', response_model=list[CommissionOut])
def list_commissions(
    db: Session = Depends(get_db),
    user_id=Depends(get_current_user_id),
) -> list[CommissionOut]:
    """List all commissions for current affiliate."""
    service = AffiliateService(db)
    affiliate = service.get_affiliate(user_id)
    if not affiliate:
        raise HTTPException(status_code=404, detail='Khong co affiliate profile')
    return [CommissionOut.model_validate(c) for c in service.list_commissions(affiliate.id)]


@router.post('/payout', response_model=PayoutOut)
def request_payout(
    payload: PayoutCreateRequest,
    db: Session = Depends(get_db),
    user_id=Depends(get_current_user_id),
) -> PayoutOut:
    """Request a payout of pending balance."""
    service = AffiliateService(db)
    affiliate = service.get_affiliate(user_id)
    if not affiliate:
        raise HTTPException(status_code=404, detail='Khong co affiliate profile')
    
    pending = service.get_pending_balance(affiliate.id)
    if payload.amount_cents > pending:
        raise HTTPException(status_code=400, detail='Payout amount exceeds pending balance')
    
    payout = service.request_payout(affiliate.id, payload)
    return PayoutOut.model_validate(payout)


@router.get('/payouts', response_model=list[PayoutOut])
def list_payouts(
    db: Session = Depends(get_db),
    user_id=Depends(get_current_user_id),
) -> list[PayoutOut]:
    """List all payouts for current affiliate."""
    service = AffiliateService(db)
    affiliate = service.get_affiliate(user_id)
    if not affiliate:
        raise HTTPException(status_code=404, detail='Khong co affiliate profile')
    return [PayoutOut.model_validate(p) for p in service.list_payouts(affiliate.id)]
