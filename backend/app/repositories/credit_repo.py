import uuid
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.credit_ledger import CreditLedger


class CreditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_balance(self, user_id: uuid.UUID) -> int:
        value = self.db.query(func.coalesce(func.sum(CreditLedger.delta_credits), 0)).filter(CreditLedger.user_id == user_id).scalar()
        return int(value or 0)

    def add_event(self, *, user_id: uuid.UUID, delta_credits: int, event_type: str, note: str | None = None, job_id=None) -> CreditLedger:
        balance_after = self.get_balance(user_id) + delta_credits
        ledger = CreditLedger(user_id=user_id, delta_credits=delta_credits, event_type=event_type, note=note, job_id=job_id, balance_after=balance_after)
        self.db.add(ledger)
        self.db.commit()
        self.db.refresh(ledger)
        return ledger

    def list(self, user_id: uuid.UUID) -> list[CreditLedger]:
        return self.db.query(CreditLedger).filter(CreditLedger.user_id == user_id).order_by(CreditLedger.created_at.desc()).limit(100).all()
