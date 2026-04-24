#!/usr/bin/env python3
"""Wait for the local stack to become healthy.

Usage: python scripts/ci/wait_for_stack.py [timeout_seconds]

Polls BASE_URL/health (or /api/v1/health) until it returns HTTP 200 or the
timeout is exceeded.  Exits 0 on success, 1 on timeout.
"""
import os
import sys
import time
import urllib.error
import urllib.request

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
HEALTH_PATHS = ["/health", "/api/v1/health", "/healthz"]


def check_health(base_url: str) -> bool:
    for path in HEALTH_PATHS:
        url = base_url.rstrip("/") + path
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                if resp.status == 200:
                    print(f"[wait_for_stack] healthy: {url}", flush=True)
                    return True
        except Exception:
            pass
    return False


def main() -> int:
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    deadline = time.time() + timeout
    interval = 5

    print(f"[wait_for_stack] waiting up to {timeout}s for {BASE_URL} ...", flush=True)
    while time.time() < deadline:
        if check_health(BASE_URL):
            return 0
        time.sleep(interval)

    print(f"[wait_for_stack] timed out after {timeout}s", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
