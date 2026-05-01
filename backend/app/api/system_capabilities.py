from fastapi import APIRouter
from app.core.provider_policy import ProviderPolicy
from app.services.provider_capability_registry import default_registry

router = APIRouter(prefix="/system", tags=["System Capabilities"])


@router.get("/capabilities")
def get_system_capabilities():
    policy = ProviderPolicy.from_env()
    reg = default_registry()
    return {
        "environment": policy.environment,
        "strict_mode": policy.strict_mode,
        "allow_placeholder_audio": policy.allow_placeholder_audio,
        "modules": reg.summary(),
    }
