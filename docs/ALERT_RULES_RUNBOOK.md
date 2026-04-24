# ALERT RULES RUNBOOK

## AudioPreviewSyntheticProbeFailed
Kiểm tra:
1. API logs
2. worker logs
3. object storage/minio
4. provider rate limit / auth

## AudioNarrationSyntheticProbeFailed
Kiểm tra thêm:
1. ffmpeg availability
2. concat list/temp storage permissions
3. queue worker backlog

## AudioQueueDepthHigh
- scale worker audio queue
- inspect stuck jobs older than 10m
- pause canary/progressive rollout

## AudioProviderFailureRateHigh
- switch provider override
- enable fallback router policy
- watch `audio_provider_failures_total`

## AudioNoSuccessfulPreviewHeartbeat
- synthetic monitor hoặc endpoint preview đang chết
- nếu deploy mới vừa xong: rollback/canary freeze
