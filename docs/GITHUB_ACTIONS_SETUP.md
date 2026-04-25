# GitHub Actions Configuration Guide

This guide explains how to set up all required secrets and workflows for the audio runtime parity patch.

## 📋 Required Secrets

Add these secrets to your GitHub repository at `Settings > Secrets and variables > Actions`.

### Monitoring & Testing Secrets

| Secret Name | Value | Example | Description |
|-------------|-------|---------|-------------|
| `MONITOR_BASE_URL` | Staging/Prod URL | `https://audio-api.example.com` | Base URL for health monitoring synthetic probes |
| `TEST_USER_EMAIL` | Test account email | `test-audio@example.com` | E2E test user email |
| `TEST_USER_PASSWORD` | Test account password | `SecurePassword123!` | E2E test user password |
| `AUDIO_E2E_EMAIL` | E2E auth email | `test-audio@example.com` | Email for E2E authentication |
| `AUDIO_E2E_PASSWORD` | E2E auth password | `SecurePassword123!` | Password for E2E authentication |
| `STAGING_BASE_URL` | Staging URL | `https://staging-audio.example.com` | Staging environment base URL |
| `STAGING_ALERTMANAGER_URL` | Alertmanager URL | `https://alertmanager-staging.example.com` | Alertmanager endpoint for chaos tests |

### Slack Integration Secrets

| Secret Name | Value | Example | Description |
|-------------|-------|---------|-------------|
| `SLACK_WEBHOOK_URL` | Slack webhook | `https://hooks.slack.com/services/T00.../B00.../XXX...` | Incoming webhook for Slack alerts |

## 🔧 Setting Up Secrets

### Step 1: Create a Slack Incoming Webhook

1. Go to your Slack workspace settings
2. Navigate to **Apps > Custom Integrations > Incoming Webhooks**
3. Click **Create New Webhook**
4. Select your target channel (e.g., `#alerts-audio`)
5. Copy the webhook URL

### Step 2: Add Secrets to GitHub

1. Go to your GitHub repository
2. Click **Settings > Secrets and variables > Actions**
3. Click **New repository secret**
4. For each secret:
   - Name (from table above)
   - Value (from your environment)
   - Click **Add secret**

### Example secrets setup:

```bash
# Using GitHub CLI
gh secret set MONITOR_BASE_URL -b "https://audio-api.example.com"
gh secret set TEST_USER_EMAIL -b "test-audio@example.com"
gh secret set TEST_USER_PASSWORD -b "SecurePassword123!"
gh secret set SLACK_WEBHOOK_URL -b "https://hooks.slack.com/services/T00.../B00.../XXX..."
```

## 📊 Workflows Overview

### 1. **audio-ci-e2e.yml** - E2E Testing
- **Trigger**: PR, push to main/master, manual dispatch
- **Tests**: Audio artifact contract, integrity checks, E2E flows
- **Secrets Used**: `AUDIO_E2E_EMAIL`, `AUDIO_E2E_PASSWORD`
- **Artifacts**: `.verify_audio_e2e/report.txt`

```yaml
# Manual dispatch with custom settings:
# - auth_enabled: Enable authentication
# - sample_path: Path to test audio file
```

### 2. **audio-health-monitor.yml** - Synthetic Monitoring
- **Trigger**: Every 10 minutes (scheduled)
- **Tests**: Preview API, narration API, health endpoint
- **Secrets Used**: `MONITOR_BASE_URL`, `TEST_USER_EMAIL`, `TEST_USER_PASSWORD`, `SLACK_WEBHOOK_URL`
- **Artifacts**: `.audio_synthetic_probe/heartbeat.prom`
- **Alerts**: Slack notification on failure

### 3. **audio-chaos-ci.yml** - Chaos Testing
- **Trigger**: Every 30 minutes (scheduled)
- **Tests**: Worker kill, provider failure, ffmpeg delay, queue backlog
- **Secrets Used**: `STAGING_BASE_URL`, `STAGING_ALERTMANAGER_URL`, `TEST_USER_EMAIL`, `TEST_USER_PASSWORD`, `SLACK_WEBHOOK_URL`
- **Scenarios**: `worker_kill,provider_fail,ffmpeg_delay,queue_backlog`

### 4. **audio-deploy-guard.yml** - Deployment Gate
- **Trigger**: Manual (before production deployment)
- **Tests**: Post-deployment audio smoke test
- **Behavior**: Blocks deployment if audio smoke fails

### 5. **audio-canary-deploy.yml** - Progressive Rollout
- **Trigger**: Manual
- **Steps**:
  1. Deploy canary version (0% traffic)
  2. Run smoke test
  3. Progressive shift: 5% → 25% → 50% → 100%
  4. Rollback on failure

### 6. **audio-regression-guard.yml** - Regression Prevention
- **Trigger**: PR
- **Tests**: Detects hardcoded values, hotfixes, compliance issues

### 7. **audio-master-verify.yml** - Master Branch Verification
- **Trigger**: Push to main/master
- **Tests**: Full audit of audio system state

## 🔔 Slack Channel Setup

### Create dedicated Slack channels:

```
#alerts-audio          - General audio system alerts
#alerts-audio-critical - Critical audio incidents
#deploy-audio          - Audio deployment notifications
#chaos-audio           - Chaos test results
#health-audio          - Health check results
```

### Update .env for Slack channels:
```bash
SLACK_CHANNEL=#alerts-audio
SLACK_CRITICAL_CHANNEL=#alerts-audio-critical
```

## 📈 Monitoring Dashboard

After secrets are set, access these monitoring interfaces:

| Service | URL | Port | Credentials |
|---------|-----|------|-------------|
| Prometheus | `http://localhost:9090` | 9090 | None |
| Grafana | `http://localhost:3001` | 3001 | admin/admin |
| Alertmanager | `http://localhost:9093` | 9093 | None |
| Flower (Celery) | `http://localhost:5555` | 5555 | None |

## ✅ Verification Checklist

- [ ] All secrets added to GitHub repository
- [ ] Slack webhook verified (test message sent)
- [ ] `audio-ci-e2e.yml` passing on PR
- [ ] `audio-health-monitor.yml` scheduled (check Actions tab)
- [ ] `audio-chaos-ci.yml` scheduled and healthy
- [ ] Slack alerts received in `#alerts-audio`
- [ ] Prometheus scraping `/api/v1/observability/prometheus`
- [ ] Grafana dashboards displaying audio metrics
- [ ] E2E test passes with artifact contract validation

## 🚀 Enabling Individual Workflows

Each workflow can be toggled in the GitHub UI:

1. Go to **Actions** tab
2. Click workflow name (e.g., "audio-ci-e2e")
3. Click **...** menu → **Enable workflow**

Or disable:
```bash
gh workflow disable audio-chaos-ci.yml
gh workflow list --all
```

## 🔐 Security Best Practices

1. **Use Organization Secrets** (for shared credentials across repos):
   - Go to Organization Settings > Secrets
   - Reference with `${{ secrets.ORG_SECRET_NAME }}`

2. **Rotate Secrets Regularly**:
   - Update test user passwords quarterly
   - Rotate Slack webhook if compromised

3. **Limit Secret Scope**:
   - Use environment-specific secrets
   - Staging and production have separate credentials

4. **Audit Access**:
   - Review GitHub audit logs periodically
   - Monitor secret access in Actions runs

## 🆘 Troubleshooting

### Workflow not triggering
- Check branch protection rules
- Verify `on:` triggers in workflow file
- Check concurrency settings (may be canceling)

### Slack notifications not sending
- Verify webhook URL is correct (test with curl)
- Check `SLACK_WEBHOOK_URL` secret is set
- Confirm Slack app permissions
- Look for error messages in workflow logs

### E2E test failures
- Check `AUDIO_E2E_EMAIL` and `AUDIO_E2E_PASSWORD`
- Verify test user exists in staging/prod
- Check if API is responding to health checks
- Review artifact contract format

### Health monitor alerts not firing
- Verify `MONITOR_BASE_URL` is reachable
- Check test credentials have access to `/api/v1/audio/health`
- Confirm Prometheus scrape interval (default: 15s)
- Check alert rules in `infra/monitoring/prometheus/rules/audio_alerts.yml`

## 📚 Additional Resources

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [Prometheus Configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
- [Alertmanager Setup](https://prometheus.io/docs/alerting/latest/configuration/)
