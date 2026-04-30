# Import all ORM models so that Base.metadata is fully populated for create_all / Alembic.
from app.models.audio_job import AudioJob  # noqa: F401
from app.models.audio_output import AudioOutput  # noqa: F401
from app.models.baseline import Baseline  # noqa: F401
from app.models.credit_ledger import CreditLedger  # noqa: F401
from app.models.decision import DecisionRecord  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.provider import Provider  # noqa: F401
from app.models.provider_capability import ProviderCapability  # noqa: F401
from app.models.remediation import LastSafePolicy, RemediationRecord, Runbook  # noqa: F401
from app.models.script_asset import ScriptAsset  # noqa: F401
from app.models.voice import Voice  # noqa: F401
from app.models.affiliate import UserAffiliate, Referral, Commission, Payout  # noqa: F401
from app.models.ai_effects import AudioEffect, UserAudioEffectPreset  # noqa: F401

__all__ = [
    "AudioJob",
    "AudioOutput",
    "AudioEffect",
    "Baseline",
    "Commission",
    "CreditLedger",
    "DecisionRecord",
    "LastSafePolicy",
    "Payout",
    "Project",
    "Provider",
    "ProviderCapability",
    "Referral",
    "RemediationRecord",
    "Runbook",
    "ScriptAsset",
    "UserAudioEffectPreset",
    "UserAffiliate",
    "Voice",
]
