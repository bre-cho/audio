from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class UserAffiliateOut(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    email: str
    referral_code: str
    bio: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class ReferralOut(BaseModel):
    id: UUID
    affiliate_id: UUID
    referred_email: str
    referred_user_id: UUID | None = None
    status: str
    created_at: datetime

    model_config = {'from_attributes': True}


class CommissionOut(BaseModel):
    id: UUID
    affiliate_id: UUID
    referral_id: UUID
    amount_cents: int
    commission_type: str
    created_at: datetime

    model_config = {'from_attributes': True}


class PayoutOut(BaseModel):
    id: UUID
    affiliate_id: UUID
    amount_cents: int
    status: str
    payout_method: str
    payout_destination: str
    requested_at: datetime
    completed_at: datetime | None = None

    model_config = {'from_attributes': True}


class PayoutCreateRequest(BaseModel):
    amount_cents: int = Field(gt=0)
    payout_method: str
    payout_destination: str
    note: str | None = None
