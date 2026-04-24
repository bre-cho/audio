# AUDIO DEPLOY GUARD PATCH

## What this adds
1. Deployment gate for audio-related production promotion
2. Post-deploy audio smoke verification
3. Automatic rollback when post-deploy audio smoke fails
4. Slack notification on block / rollback

## Minimal integration
- Keep your existing deploy workflow untouched
- Call `audio-deploy-guard.yml` before production promotion
- Or merge the `deploy_guard.sh` invocation into your current deploy job

## Required integration points
- `DEPLOY_COMMAND`: existing deployment command
- `ROLLBACK_COMMAND`: explicit rollback command, strongly preferred
- `verify_audio_e2e.sh`: already created in prior steps
- `SLACK_WEBHOOK_URL`: Slack incoming webhook secret

## Safest rollout
- First enable only for `staging`
- Then add `production` environment protection
- Then wire required checks + approvers on the environment
