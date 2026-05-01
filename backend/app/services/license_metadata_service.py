from __future__ import annotations


def require_license_metadata(meta: dict) -> dict:
    required = ["license_type", "commercial_use", "source_provider"]
    missing = [k for k in required if k not in meta]
    if missing:
        raise ValueError(f"license_metadata_missing:{','.join(missing)}")
    return meta
