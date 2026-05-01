from fastapi import HTTPException


def deprecated_endpoint(name: str, replacement: str):
    raise HTTPException(
        status_code=410,
        detail={
            "error": "deprecated_endpoint",
            "endpoint": name,
            "replacement": replacement,
            "rule": "Use canonical v2 route. Deprecated routes must not fake-queue jobs.",
        },
    )
