from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.production_truth import assert_runtime_truth

router = APIRouter()


class RuntimeTruthRequest(BaseModel):
    provider: str
    capability: str


@router.post("/check")
def check_runtime_truth(payload: RuntimeTruthRequest):
    decision = assert_runtime_truth(payload.provider, payload.capability)
    if not decision.allowed:
        raise HTTPException(status_code=409, detail=decision.__dict__)
    return decision.__dict__
