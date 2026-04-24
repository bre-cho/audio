# AUDIO HEALTH MONITOR PATCH

## 1. Patch backend metrics
Bổ sung metric audio vào endpoint observability/prometheus hiện có:
- `audio_preview_requests_total{status,provider}`
- `audio_preview_latency_seconds_bucket{provider}`
- `audio_narration_jobs_total{status,provider}`
- `audio_narration_job_latency_seconds_bucket{provider}`
- `audio_voice_clone_jobs_total{status,provider}`
- `audio_voice_clone_queue_depth`
- `audio_narration_queue_depth`
- `audio_audio_mix_queue_depth`
- `audio_jobs_stuck_total{job_type}`
- `audio_provider_failures_total{provider,operation,error_code}`
- `audio_preview_last_success_timestamp_seconds`
- `audio_narration_last_success_timestamp_seconds`
- `audio_clone_last_success_timestamp_seconds`

## 2. Prometheus scrape targets
- API metrics endpoint
- blackbox probe for `/health` and `/api/v1/audio/health`
- optional Celery exporter / redis exporter
- node exporter / cadvisor

## 3. Alerting policy
Severity:
- `warning`: latency cao, queue tăng, 1 provider fail rải rác
- `critical`: synthetic preview/narration fail, stuck jobs tăng mạnh, không có success heartbeat, rollback gate block

## 4. Grafana
Dashboard gồm 6 hàng:
- Availability
- Synthetic checks
- Queue + backlog
- Provider health
- Job latency + errors
- Business events
