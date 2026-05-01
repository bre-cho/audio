from dataclasses import dataclass
from typing import Literal

CloneMode = Literal["instant_clone", "professional_clone", "rvc_upload"]


@dataclass(frozen=True)
class CloneModePolicy:
    mode: CloneMode
    min_sample_sec: int
    requires_consent: bool = True
    requires_provider_polling: bool = True


class CloneModeService:
    POLICIES = {
        "instant_clone": CloneModePolicy("instant_clone", min_sample_sec=30),
        "professional_clone": CloneModePolicy("professional_clone", min_sample_sec=300),
        "rvc_upload": CloneModePolicy("rvc_upload", min_sample_sec=0, requires_provider_polling=False),
    }

    def get_policy(self, mode: CloneMode) -> CloneModePolicy:
        if mode not in self.POLICIES:
            raise ValueError(f"Unsupported clone mode: {mode}")
        return self.POLICIES[mode]
