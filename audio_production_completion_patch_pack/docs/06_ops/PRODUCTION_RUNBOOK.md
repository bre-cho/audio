# PRODUCTION RUNBOOK — AI AUDIO FACTORY

## 1. Env bắt buộc

```bash
ENV=production
PROVIDER_STRICT_MODE=true
ALLOW_PLACEHOLDER_AUDIO=false
ALLOW_PROVIDER_FALLBACK=false
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
STORAGE_BACKEND=s3
```

Provider keys:
```bash
ELEVENLABS_API_KEY=...
MINIMAX_API_KEY=...
```
Chỉ bật provider khi implementation thật đã pass CI.

## 2. Healthcheck bắt buộc
- API alive
- Postgres connected
- Redis connected
- Celery worker active
- Storage write/read/delete
- Provider auth check
- Queue depth
- Failed job ratio

## 3. Monitoring metrics
- jobs_total by feature/status/provider
- audio_generation_duration_seconds
- provider_error_total
- artifact_validation_failed_total
- silent_audio_blocked_total
- queue_depth
- worker_heartbeat_age_seconds
- storage_write_failed_total

## 4. Incident playbook

### Provider outage
- Disable provider routing.
- Do not fallback to placeholder.
- Mark jobs retrying only if provider outage is transient.
- Alert operator.

### Silent artifact detected
- Block promotion.
- Quarantine artifact.
- Mark job failed.
- Attach quality report.

### Clone consent missing
- Reject request.
- No file persisted unless policy allows temporary encrypted staging.

### Worker stuck
- Check Redis queue.
- Check Celery heartbeat.
- Requeue only idempotent jobs.
- Never duplicate billing/credits without idempotency key.

## 5. Release gate
Không release nếu chưa pass:
- provider capability verification
- audio signal validation
- worker E2E
- DB migration fresh install
- frontend route parity
