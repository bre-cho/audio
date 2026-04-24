# Secrets and Env

## GitHub Secrets
- `SLACK_WEBHOOK_URL`
- `TEST_USER_EMAIL`
- `TEST_USER_PASSWORD`

## GitHub Variables
- `DEPLOY_COMMAND`
- `ROLLBACK_COMMAND`
- `BASE_URL`
- `AUDIO_HEALTH_URL`
- `PREVIOUS_REVISION`
- `AUTH_ENABLED`
- `SAMPLE_PATH`

## Notes
- Prefer storing `DEPLOY_COMMAND` and `ROLLBACK_COMMAND` in environment-level variables.
- Prefer an explicit rollback command over inferring rollback from git state.
