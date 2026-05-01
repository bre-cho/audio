from fastapi import APIRouter
from app.services.provider_capability_gate_v2 import capability_matrix

router = APIRouter()


@router.get("")
def get_system_capabilities_v2():
    return {"capabilities": capability_matrix()}
