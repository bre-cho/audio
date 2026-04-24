# PATCH MAP 3-5 DÒNG / FILE

## backend/app/services/observability_metrics.py
- append audio metrics vào `collect_status_snapshot()`
- export thêm queue depth + stuck jobs + provider failures + success heartbeat
- giữ nguyên render metrics cũ, chỉ append

## backend/app/api/observability.py hoặc router hiện có
- expose `/api/v1/audio/health`
- expose audio synthetic-ready status payload
- nếu đã có `/api/v1/observability/prometheus` thì chỉ cần thêm sample audio metrics

## docker-compose monitoring stack
- mount `infra/monitoring/prometheus/prometheus.audio.yml`
- mount `infra/monitoring/prometheus/rules/audio_alerts.yml`
- mount Grafana dashboard/audio provisioning

## CI
- add workflow `.github/workflows/audio-health-monitor.yml`
- schedule 10 phút/lần
- failure -> artifact + Slack
