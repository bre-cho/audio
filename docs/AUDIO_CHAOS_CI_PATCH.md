# AUDIO_CHAOS_CI_PATCH

## Minimal patch
Add this file to:
`.github/workflows/audio-chaos-ci.yml`

## Expected alert mapping
- `worker_kill` -> `AudioNarrationStuckJobs`, `AudioHealthEndpointDown`
- `provider_fail` -> `AudioNarrationProviderFailureRateHigh`, `AudioPreviewProviderFailureRateHigh`
- `ffmpeg_delay` -> `AudioMergeHighLatency`
- `queue_backlog` -> `AudioNarrationStuckJobs`

## Notes
- The workflow is scheduled every 30 minutes by default.
- It uses `actions/checkout@v6`, `actions/setup-python@v6`, `actions/upload-artifact@v6`, and `slackapi/slack-github-action@v3`, which match current upstream majors. 
- If your staging chaos test must run from a self-hosted runner inside the target network, change `runs-on`.
