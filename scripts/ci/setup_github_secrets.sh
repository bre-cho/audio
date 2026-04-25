#!/usr/bin/env bash
set -euo pipefail

# GitHub Actions Secrets Setup Helper
# This script helps configure required secrets for audio system workflows

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_URL="${GH_REPO_URL:-}"

usage() {
  cat >&2 <<'EOF'
Usage: bash scripts/ci/setup_github_secrets.sh [OPTIONS]

Options:
  --help                    Show this help message
  --list-required           List all required secrets
  --check                   Check which secrets are already set
  --test-webhook            Test Slack webhook connectivity
  --generate-template       Generate a .env.secrets template

Examples:
  bash scripts/ci/setup_github_secrets.sh --list-required
  bash scripts/ci/setup_github_secrets.sh --check
  bash scripts/ci/setup_github_secrets.sh --test-webhook
EOF
  exit 1
}

list_required_secrets() {
  echo "=== Required GitHub Secrets ==="
  echo ""
  echo "Monitoring & Testing:"
  echo "  MONITOR_BASE_URL           - Staging/Prod URL for health monitoring"
  echo "  TEST_USER_EMAIL            - E2E test user email"
  echo "  TEST_USER_PASSWORD         - E2E test user password"
  echo "  AUDIO_E2E_EMAIL            - E2E auth email"
  echo "  AUDIO_E2E_PASSWORD         - E2E auth password"
  echo "  STAGING_BASE_URL           - Staging environment base URL"
  echo "  STAGING_ALERTMANAGER_URL   - Alertmanager endpoint for chaos tests"
  echo ""
  echo "Slack Integration:"
  echo "  SLACK_WEBHOOK_URL          - Slack incoming webhook for alerts"
  echo ""
}

check_secrets() {
  if ! command -v gh &>/dev/null; then
    echo "ERROR: GitHub CLI (gh) not found. Install from https://cli.github.com/"
    exit 1
  fi

  echo "=== Checking GitHub Secrets ==="
  echo ""

  secrets_to_check=(
    "MONITOR_BASE_URL"
    "TEST_USER_EMAIL"
    "TEST_USER_PASSWORD"
    "AUDIO_E2E_EMAIL"
    "AUDIO_E2E_PASSWORD"
    "STAGING_BASE_URL"
    "STAGING_ALERTMANAGER_URL"
    "SLACK_WEBHOOK_URL"
  )

  if gh secret list >/dev/null 2>&1; then
    existing="$(gh secret list --json name -q '.[].name' 2>/dev/null || echo "")"
    found_count=0

    for secret in "${secrets_to_check[@]}"; do
      if echo "$existing" | grep -q "^${secret}$"; then
        echo "✓ $secret is set"
        ((found_count++))
      else
        echo "✗ $secret is NOT set"
      fi
    done

    echo ""
    echo "Summary: $found_count/${#secrets_to_check[@]} secrets configured"
  else
    echo "ERROR: Cannot access repository secrets. Make sure you're logged in with 'gh auth login'"
    exit 1
  fi
}

test_webhook() {
  local webhook_url="${1:-}"

  if [[ -z "$webhook_url" ]]; then
    echo "Test Slack Webhook Connectivity"
    echo ""
    echo "Usage: bash ..setupname path_to_setup.sh --test-webhook 'YOUR_WEBHOOK_URL'"
    echo ""
    echo "Or set SLACK_WEBHOOK_URL environment variable:"
    echo "  export SLACK_WEBHOOK_URL='https://hooks.slack.com/...'"
    echo "  bash scripts/ci/setup_github_secrets.sh --test-webhook"
    return 1
  fi

  echo "Testing Slack webhook: ${webhook_url:0:50}..."
  response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$webhook_url" \
    -H 'Content-Type: application/json' \
    -d '{
      "text": "✓ Audio system Slack webhook is working!",
      "blocks": [
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": "✓ *Audio Webhook Test Successful*\nTime: '"$(date)"'\nFrom: GitHub Actions Setup"
          }
        }
      ]
    }')

  if [[ "$response" == "200" ]]; then
    echo "✓ Slack webhook is working correctly (HTTP 200)"
    return 0
  else
    echo "✗ Slack webhook test failed (HTTP $response)"
    echo "Please check:"
    echo "  1. Webhook URL is correct"
    echo "  2. Channel exists and bot has permission"
    echo "  3. Slack workspace is active"
    return 1
  fi
}

generate_template() {
  cat > "$SCRIPT_DIR/.env.secrets.template" <<'TEMPLATE'
# GitHub Secrets Template
# Copy this file to .env.secrets and fill in the values
# Then use: gh secret set VAR_NAME < .env.secrets

# Monitoring & Testing
MONITOR_BASE_URL=https://audio-api.example.com
TEST_USER_EMAIL=test-audio@example.com
TEST_USER_PASSWORD=SecureTestPassword123!
AUDIO_E2E_EMAIL=test-audio@example.com
AUDIO_E2E_PASSWORD=SecureTestPassword123!
STAGING_BASE_URL=https://staging-audio.example.com
STAGING_ALERTMANAGER_URL=https://alertmanager-staging.example.com

# Slack Integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/PLACEHOLDER/CHANGE_ME/PLACEHOLDER
TEMPLATE

  echo "✓ Created .env.secrets.template"
  echo ""
  echo "Next steps:"
  echo "  1. Edit .env.secrets.template with your values"
  echo "  2. Source and set secrets:"
  echo "     source .env.secrets.template"
  echo "     gh secret set MONITOR_BASE_URL -b \"$MONITOR_BASE_URL\""
  echo "  3. Verify with:"
  echo "     bash scripts/ci/setup_github_secrets.sh --check"
}

enable_workflows() {
  local workflows=(
    "audio-ci-e2e.yml"
    "audio-health-monitor.yml"
    "audio-chaos-ci.yml"
    "audio-deploy-guard.yml"
    "audio-canary-deploy.yml"
  )

  echo "=== Enabling Audio Workflows ==="
  for workflow in "${workflows[@]}"; do
    if gh workflow enable "$workflow" 2>/dev/null; then
      echo "✓ Enabled $workflow"
    else
      echo "! Could not enable $workflow (may already be enabled)"
    fi
  done
}

main() {
  case "${1:-}" in
    --help)
      usage
      ;;
    --list-required)
      list_required_secrets
      ;;
    --check)
      check_secrets
      ;;
    --test-webhook)
      test_webhook "${2:-$SLACK_WEBHOOK_URL}"
      ;;
    --generate-template)
      generate_template
      ;;
    --enable-workflows)
      enable_workflows
      ;;
    *)
      usage
      ;;
  esac
}

main "$@"
