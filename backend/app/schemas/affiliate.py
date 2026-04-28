from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

_ALLOWED_PAYOUT_METHODS = {"paypal", "bank_transfer", "crypto_usdc"}
_MIN_PAYOUT_CENTS = 1000       # $10 minimum
_MAX_PAYOUT_CENTS = 10_000_00  # $10,000 maximum single payout


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

    @field_validator('amount_cents')
    @classmethod
    def validate_amount(cls, v: int) -> int:
        if v < _MIN_PAYOUT_CENTS:
            raise ValueError(f'Minimum payout is ${_MIN_PAYOUT_CENTS // 100}')
        if v > _MAX_PAYOUT_CENTS:
            raise ValueError(f'Maximum single payout is ${_MAX_PAYOUT_CENTS // 100}')
        return v

    @field_validator('payout_method')
    @classmethod
    def validate_method(cls, v: str) -> str:
        if v.lower() not in _ALLOWED_PAYOUT_METHODS:
            raise ValueError(f'Allowed payout methods: {sorted(_ALLOWED_PAYOUT_METHODS)}')
        return v.lower()

    @field_validator('payout_destination')
    @classmethod
    def validate_destination(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('payout_destination cannot be empty')
        if len(v) > 256:
            raise ValueError('payout_destination too long (max 256 chars)')
        return v
