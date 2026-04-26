# Checklist v40 → v76

## Global

```bash
bash -n scripts/ci/verify_audio_patch.sh
bash -n scripts/ci/verify_audio_e2e.sh
```

## Verify Safety

```bash
VERIFY_RUNTIME=0 SKIP_STACK_UP=1 bash scripts/ci/verify_audio_patch.sh
VERIFY_RUNTIME=1 SKIP_STACK_UP=1 bash scripts/ci/verify_audio_patch.sh
SKIP_STACK_UP=1 bash scripts/ci/verify_audio_e2e.sh
```

Pass khi:

- report không bị ghi đè.
- grep path thiếu folder không làm script chết sai.
- API fail thì report có `[FAIL]`.
- project_id rỗng/null thì dừng ngay.
- không có pass giả qua `|| true`, pipeline, subshell.

## Artifact Gate

Pass khi artifact có:

- `artifact_id`
- `artifact_type`
- `path` hoặc `url`
- `mime_type`
- `size_bytes > 0`
- `checksum`
- `created_at`
- `source_job_id`
- lineage đầy đủ
- replay dry-run pass
- determinism/drift budget pass
- promotion gate pass
- authority + no bypass pass

## Regression & Baseline

Pass khi:

- baseline nằm trong registry.
- baseline active, chưa expired, chưa frozen.
- nightly replay ổn định.
- drift vượt budget thì freeze + incident.
- candidate phải qua canary.
- canary fail thì auto rollback.
- confidence score không dùng nếu thiếu sample/segment coverage.

## Policy & Evolution

Pass khi:

- mọi decision có decision record.
- policy candidate qua sandbox.
- tournament có nhiều policy và cùng scenario set.
- diversity guard chặn duplicate policy.
- mutation có seed, parent, generation.
- kill-switch có last safe policy.
- policy unsafe không được promote.

## Recovery & Autonomous

Pass khi:

- recovery drill pass.
- recovery SLO pass.
- runbook được tạo nếu drill fail.
- runbook phải verify thật.
- autonomous remediation chỉ chạy trong safe envelope.
- approval tier chặn high/critical risk.
