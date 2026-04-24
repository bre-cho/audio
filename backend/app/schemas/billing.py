from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class BillingBalanceOut(BaseModel):
    balance_credits: int


class CreditLedgerOut(BaseModel):
    id: UUID
    delta_credits: int
    event_type: str
    balance_after: int | None = None
    note: str | None = None
    created_at: datetime

    model_config = {'from_attributes': True}


class UsageEstimateRequest(BaseModel):
    unit_type: str
    units: int


class UsageEstimateOut(BaseModel):
    units: int
    unit_type: str
    estimated_credits: int
