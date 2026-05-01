#!/usr/bin/env bash
set -euo pipefail
cat <<'TXT'
AUDIO PRODUCTION COMPLETION PATCH PACK V4

1. Copy backend/app/* into repo backend/app/.
2. Copy frontend/src/* into repo frontend/src/.
3. Copy tests/* into repo tests/.
4. Wire backend/app/api/canonical_routes.py from your main API router.
5. Mark old v1 routes deprecated or wrappers.
6. Run:
   pytest tests/test_no_fake_queued_routes.py tests/test_provider_single_source.py tests/test_unified_audio_qa_pipeline.py
TXT
