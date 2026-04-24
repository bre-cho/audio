from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.billing import BillingBalanceOut, CreditLedgerOut, UsageEstimateRequest, UsageEstimateOut
from app.services.billing_service import BillingService

router = APIRouter()


@router.get('/balance', response_model=BillingBalanceOut)
def get_balance(db: Session = Depends(get_db)) -> BillingBalanceOut:
    return BillingService(db).get_balance()


@router.get('/ledger', response_model=list[CreditLedgerOut])
def get_ledger(db: Session = Depends(get_db)) -> list[CreditLedgerOut]:
    return BillingService(db).get_ledger()


@router.post('/estimate', response_model=UsageEstimateOut)
def estimate_usage(payload: UsageEstimateRequest, db: Session = Depends(get_db)) -> UsageEstimateOut:
    return BillingService(db).estimate(payload)
