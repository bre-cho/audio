# PATCH 3-5 LINES TO CONNECT THIS INTO EXISTING FLOWS

## After chaos/deploy failure, trigger incident report
```yaml
- name: Trigger incident report
  if: failure()
  uses: peter-evans/repository-dispatch@v3
  with:
    event-type: audio_incident_report
    client-payload: '{"incident_context":"audio-chaos-failure","alertname":"AudioChaosFailure","severity":"critical"}'
```

The included workflow also listens to workflow_run failures from:
- audio-chaos-ci
- audio-ci-e2e
- audio-canary-deploy
