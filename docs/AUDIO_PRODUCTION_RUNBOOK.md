# AUDIO PRODUCTION RUNBOOK

## Environment bat buoc
- APP_ENV=production
- PROVIDER_STRICT_MODE=true
- ALLOW_PLACEHOLDER_AUDIO=false
- ALLOW_PROVIDER_FALLBACK=false
- DATABASE_URL, REDIS_URL hop le

## Release gate
1. Chay scripts/ci/verify_audio_truth_gate.sh
2. Chay scripts/ci/verify_provider_capabilities.sh
3. Chay scripts/ci/verify_worker_e2e.sh
4. Chay scripts/ci/verify_frontend_api_parity.py
5. Chay full test backend

## Incident handling
- Provider outage: khong fallback sang placeholder, mark retry co dieu kien.
- Silent artifact detected: block promotion, mark failed.
- Worker stuck: kiem tra queue/heartbeat, chi requeue job idempotent.
