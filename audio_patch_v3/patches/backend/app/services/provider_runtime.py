from __future__ import annotations

import importlib
from typing import Any

from app.providers.unified_provider_registry import resolve_provider


def load_provider_adapter(capability: str, provider: str | None = None, *args: Any, **kwargs: Any) -> Any:
    binding = resolve_provider(capability, provider)
    module_name, class_name = binding.adapter_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    return cls(*args, **kwargs)
