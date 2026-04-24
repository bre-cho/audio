# PATCH MAP 3-5 lines

## docker-compose / scripts layout
Copy `scripts/chaos/audio_chaos_test.sh` into your repo at `scripts/chaos/audio_chaos_test.sh`.

## CI / workflow add-on
```yaml
- name: Audio chaos test
  if: github.ref == 'refs/heads/main'
  run: bash scripts/chaos/audio_chaos_test.sh
```

## Staging-safe run
Set `SCENARIOS=worker_kill,provider_fail` first. Add `ffmpeg_delay,queue_backlog` only after alerts are confirmed to route correctly.

## Expected alerts
- worker_kill -> AudioNarrationStuckJobs or AudioNarrationTrafficWithoutSuccess
- provider_fail -> AudioPreviewProviderFailureRateHigh or AudioNarrationProviderFailureRateHigh
- ffmpeg_delay -> AudioMergeHighLatency or AudioNarrationHighLatencyP50Approx
- queue_backlog -> AudioNarrationStuckJobs or AudioHealthEndpointDown
