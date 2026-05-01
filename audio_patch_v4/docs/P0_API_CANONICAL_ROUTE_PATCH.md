# P0 — API Canonical Route Patch

Problem: repo has parallel v1/v2 routes such as `transcription.py` and `transcription_v2.py`, `podcast.py` and `podcast_v2.py`. This creates split behavior.

Rules:

```txt
canonical = v2
v1 = deprecated wrapper
no fake queued
not ready = HTTP 409
ready = real job id + persisted job row
```

Implementation:

1. Add `backend/app/api/canonical_routes.py`.
2. Import only canonical route modules in the production router.
3. Old v1 route must call `deprecated_endpoint()` and forward to canonical service or return 410/409.
4. Tests must scan all route functions for `return {"status": "queued"}` without a real job creation call.
