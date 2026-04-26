# Contract Summary

## Artifact Contract

```json
{
  "artifact_id": "string",
  "artifact_type": "audio_preview|audio_render|final_mix",
  "path": "string|null",
  "url": "string|null",
  "mime_type": "audio/mpeg|audio/wav",
  "size_bytes": 123,
  "checksum": "sha256",
  "created_at": "ISO-8601",
  "source_job_id": "string",
  "project_id": "string",
  "preview_id": "string|null",
  "scene_id": "string|null",
  "render_id": "string|null",
  "input_hash": "sha256",
  "provider": "string",
  "template_version": "string",
  "runtime_version": "string",
  "provider_config_hash": "sha256",
  "promotion_status": "candidate|promoted|frozen",
  "promotion_actor": "string",
  "promotion_role": "ci|system|worker",
  "promotion_source": "ci|worker",
  "promotion_hash": "sha256"
}
```

## Baseline Contract

```json
{
  "baseline_id": "string",
  "artifact_id": "string",
  "baseline_type": "golden|canary|regression",
  "owner": "string",
  "approved_by": "string",
  "created_at": "ISO-8601",
  "retention_days": 90,
  "replay_schedule": "nightly",
  "drift_budget_policy": "string",
  "status": "active|deprecated|frozen",
  "lifecycle_state": "candidate|canary_active|active|deprecated|frozen|archived",
  "expires_at": "ISO-8601"
}
```

## Decision Contract

```json
{
  "decision_id": "string",
  "trigger_type": "canary_failure|regression_drift|manual|scheduled",
  "scenarios_considered": [],
  "selected_action": "rollback|fallback|partial_freeze|delay|promote",
  "rejected_actions": [],
  "score_breakdown": {},
  "selected_reason": "string",
  "confidence_score": 90,
  "policy_version": "string",
  "decision_engine_version": "string",
  "approved_by": "system",
  "decision_actor": "system|ci|operator",
  "execution_status": "pending|executed|failed",
  "outcome_tracking_id": "string",
  "decision_hash": "sha256",
  "immutable": true
}
```

## Remediation Contract

```json
{
  "remediation_id": "string",
  "trigger_source": "regression|canary|incident|slo_breach",
  "runbook_id": "string",
  "action_plan": [],
  "auto_apply_allowed": false,
  "risk_level": "low|medium|high|critical",
  "blast_radius_estimate": "low|medium|high|critical",
  "confidence_score": 90,
  "execution_status": "pending|running|succeeded|failed",
  "verification_status": "pending|pass|fail",
  "rollback_triggered": false,
  "human_override_required": false,
  "approval_tier": "tier_0|tier_1|tier_2|tier_3",
  "execution_allowed": false
}
```
