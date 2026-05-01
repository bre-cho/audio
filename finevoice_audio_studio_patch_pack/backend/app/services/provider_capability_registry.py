from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ProviderCapability:
    provider: str
    module: str
    status: str  # ready | degraded | blocked
    reason: Optional[str] = None


class ProviderCapabilityRegistry:
    def __init__(self) -> None:
        self._items: Dict[str, ProviderCapability] = {}

    def register(self, provider: str, module: str, status: str, reason: Optional[str] = None) -> None:
        if status not in {"ready", "degraded", "blocked"}:
            raise ValueError("status must be ready, degraded, or blocked")
        self._items[f"{provider}:{module}"] = ProviderCapability(provider, module, status, reason)

    def get(self, provider: str, module: str) -> ProviderCapability:
        return self._items.get(
            f"{provider}:{module}",
            ProviderCapability(provider=provider, module=module, status="blocked", reason="capability_not_registered"),
        )

    def assert_ready(self, provider: str, module: str, allow_degraded: bool = False) -> None:
        cap = self.get(provider, module)
        if cap.status == "ready":
            return
        if allow_degraded and cap.status == "degraded":
            return
        raise RuntimeError(f"Provider capability blocked: {provider}/{module}: {cap.reason or cap.status}")

    def summary(self) -> Dict[str, Dict]:
        modules: Dict[str, Dict] = {}
        for cap in self._items.values():
            bucket = modules.setdefault(cap.module, {"status": "blocked", "providers": [], "reasons": []})
            bucket["providers"].append(cap.provider)
            if cap.status == "ready":
                bucket["status"] = "ready"
            elif cap.status == "degraded" and bucket["status"] != "ready":
                bucket["status"] = "degraded"
            if cap.reason:
                bucket["reasons"].append({cap.provider: cap.reason})
        return modules


def default_registry() -> ProviderCapabilityRegistry:
    reg = ProviderCapabilityRegistry()
    reg.register("elevenlabs", "tts", "ready")
    reg.register("elevenlabs", "voice_clone", "blocked", "clone_upload_polling_not_wired")
    reg.register("minimax", "tts", "blocked", "provider_not_implemented")
    reg.register("internal_genvoice", "tts", "blocked", "placeholder_provider")
    reg.register("local_dsp", "voice_changer", "degraded", "pitch_shift_only")
    reg.register("local_dsp", "noise_reduction", "blocked", "rnnoise_or_demucs_not_wired")
    return reg
