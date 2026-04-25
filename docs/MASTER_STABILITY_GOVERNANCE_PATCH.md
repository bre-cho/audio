# MASTER STABILITY & GOVERNANCE PATCH

This patch consolidates the previous incremental verify/artifact hardening ideas into one repo-level implementation.

## What changed

1. Verify scripts now use strict execution, append-only reports, guarded grep paths, and assertion helpers.
2. Audio artifact writer now returns a full artifact contract, including size, sha256 checksum, lineage, replay metadata, and promotion flags.
3. Worker `runtime_json` stores the artifact contracts and promotion gate result, so `/api/v1/jobs/{id}` is the single read model for downstream checks.
4. E2E now validates state, output format, artifact HTTP reachability, size, checksum format, lineage, replayability, determinism, drift budget, and promotion gate.

## Verify

```bash
bash -n scripts/ci/verify_audio_patch.sh
bash -n scripts/ci/verify_audio_e2e.sh
VERIFY_RUNTIME=0 SKIP_STACK_UP=1 bash scripts/ci/verify_audio_patch.sh
VERIFY_RUNTIME=1 SKIP_STACK_UP=1 bash scripts/ci/verify_audio_patch.sh
SKIP_STACK_UP=1 bash scripts/ci/verify_audio_e2e.sh
```

## Artifact contract

Each generated artifact includes:

```text
artifact_id
artifact_type
path
url
mime_type
size_bytes
checksum
created_at
source_job_id
input_hash
provider
model_version
template_version
runtime_version
contract_pass
lineage_pass
replayability_pass
determinism_pass
drift_budget_pass
promotion_status
```
