"""Lightweight in-process IP-based rate limiter.

Uses a sliding window counter stored in a module-level dict.
Thread-safe via a threading.Lock. Suitable for single-worker deployments;
for multi-worker/multi-process, replace bucket_store with Redis.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from typing import Callable

from fastapi import HTTPException, Request, status


_lock = threading.Lock()
# bucket_store: key -> deque of request timestamps
_bucket_store: dict[str, deque] = {}


def _get_client_ip(request: Request) -> str:
    """Extract real client IP, honouring X-Forwarded-For if present."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(max_requests: int, window_seconds: int) -> Callable:
    """Return a FastAPI dependency that enforces a per-IP sliding-window rate limit.

    Usage::

        @router.get('/some-route')
        def handler(_: None = Depends(rate_limit(10, 60))):
            ...
    """

    def dependency(request: Request) -> None:
        ip = _get_client_ip(request)
        bucket_key = f"{request.url.path}:{ip}"
        now = time.monotonic()
        window_start = now - window_seconds

        with _lock:
            if bucket_key not in _bucket_store:
                _bucket_store[bucket_key] = deque()
            bucket = _bucket_store[bucket_key]

            # Remove timestamps outside the current window
            while bucket and bucket[0] < window_start:
                bucket.popleft()

            if len(bucket) >= max_requests:
                retry_after = int(window_seconds - (now - bucket[0])) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later.",
                    headers={"Retry-After": str(retry_after)},
                )

            bucket.append(now)

    return dependency
