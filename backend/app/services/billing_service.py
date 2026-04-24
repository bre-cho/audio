import uuid
from sqlalchemy.orm import Session
from app.core.credits import CreditPolicy
from app.repositories.credit_repo import CreditRepository
from app.schemas.billing import BillingBalanceOut, CreditLedgerOut, UsageEstimateRequest, UsageEstimateOut


class BillingService:
    def __init__(self, db: Session) -> None:
        self.repo = CreditRepository(db)
        self.default_user_id = uuid.UUID('00000000-0000-0000-0000-000000000001')

    def get_balance(self) -> BillingBalanceOut:
        return BillingBalanceOut(balance_credits=self.repo.get_balance(self.default_user_id))

    def get_ledger(self) -> list[CreditLedgerOut]:
        return [CreditLedgerOut.model_validate(item) for item in self.repo.list(self.default_user_id)]

    def estimate(self, payload: UsageEstimateRequest) -> UsageEstimateOut:
        if payload.unit_type == 'chars':
            return CreditPolicy.estimate_tts(payload.units)
        return UsageEstimateOut(units=payload.units, unit_type=payload.unit_type, estimated_credits=0)
