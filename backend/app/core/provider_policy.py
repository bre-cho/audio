import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderPolicy:
    strict_mode: bool
    allow_placeholder_audio: bool
    block_internal_genvoice_in_prod: bool
    environment: str

    @classmethod
    def from_env(cls) -> "ProviderPolicy":
        return cls(
            strict_mode=os.getenv("PROVIDER_STRICT_MODE", "true").lower() == "true",
            allow_placeholder_audio=os.getenv("ALLOW_PLACEHOLDER_AUDIO", "false").lower() == "true",
            block_internal_genvoice_in_prod=os.getenv("BLOCK_INTERNAL_GENVOICE_IN_PROD", "true").lower() == "true",
            environment=os.getenv("APP_ENV", os.getenv("ENV", "development")).lower(),
        )

    def assert_provider_allowed(self, provider: str, generation_mode: str = "real") -> None:
        provider_name = (provider or "").lower().strip()
        mode = (generation_mode or "").lower().strip()
        is_prod = self.environment in {"prod", "production"}

        if self.strict_mode and mode in {"placeholder", "mock", "silent", "degraded"} and not self.allow_placeholder_audio:
            raise RuntimeError(f"Audio generation mode '{mode}' is blocked by provider policy")

        if is_prod and self.block_internal_genvoice_in_prod and provider_name in {"internal", "internal_genvoice", "mock"}:
            raise RuntimeError("internal_genvoice/mock provider is blocked in production")
