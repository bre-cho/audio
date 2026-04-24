#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

NEXT_ACTIONS = {
    "provider_failure": "- Check provider status / upstream API quota / retry policy.",
    "queue_backlog": "- Check Celery worker health, Redis latency, queue depth, stuck jobs.",
    "ffmpeg_failure": "- Check input media integrity, codec handling, ffmpeg command args.",
    "infra_down": "- Check container/node/network/storage health.",
    "test_regression": "- Inspect latest code diff and failing assertions.",
    "unknown": "- No strong signal found. Inspect workflow logs manually.",
}


def _fmt_list(items):
    return "\n".join(f"- {x}" for x in items) if items else "_none_"


def _fmt_dict(d):
    return "\n".join(f"- {k}: {v}" for k, v in d.items()) if d else "_none_"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classification", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    data = json.loads(Path(args.classification).read_text(encoding="utf-8"))
    root = data.get("root_cause", "unknown")
    confidence = data.get("confidence", 0.0)
    secondary_cause = data.get("secondary_cause")
    evidence_lines = _fmt_list(data.get("evidence", []))
    ranked_lines = "\n".join(
        f"- {x['cause']}: {x['score']}" for x in data.get("ranked_causes", [])
    ) or _fmt_dict(data.get("scores", {}))

    # v5 — recommended actions
    actions = data.get("recommended_actions", {})
    primary_act = actions.get("primary", {})
    secondary_act = actions.get("secondary")
    first_cmd = (primary_act.get("commands") or ["inspect logs"])[0]
    first_owner = (primary_act.get("owners") or ["oncall"])[0]
    primary_cmds = _fmt_list(primary_act.get("commands", []))
    primary_dash = _fmt_list(primary_act.get("dashboards", []))
    primary_srv = _fmt_list(primary_act.get("services", []))
    primary_own = _fmt_list(primary_act.get("owners", []))

    # v6 — linked resources
    links = data.get("linked_resources", {})
    link_primary = links.get("primary", {})
    link_secondary = links.get("secondary")
    runbook = link_primary.get("runbook", "")
    click_first = runbook or next(iter(link_primary.get("dashboards", {}).values()), "")
    dash_lines = _fmt_dict(link_primary.get("dashboards", {}))
    log_lines = _fmt_dict(link_primary.get("logs", {}))
    chat_lines = _fmt_dict(link_primary.get("chat", {}))

    # v7 — escalation
    esc = data.get("escalation", {})
    esc_mode = esc.get("mode", "channel_only")
    esc_sev = esc.get("severity", "P3")
    esc_team = esc.get("mention_team", "oncall")
    dedupe_key = data.get("dedupe_key", "")

    # v8 — repeat incident
    repeat = data.get("repeat_incident", {})
    repeat_count = repeat.get("repeat_count_30m", 1)
    repeat_override = repeat.get("override_applied", False)

    # v9 — storm control
    storm = data.get("storm_control", {})
    storm_active = storm.get("active", False)
    storm_count = storm.get("cluster_count_30m", 1)
    storm_reason = storm.get("reason")
    cluster_key = data.get("cluster_key", "")

    # v10 — parent incident lifecycle
    parent = data.get("parent_incident", {})
    child = data.get("child_incident", {})
    parent_key = parent.get("parent_incident_key", "")
    parent_status_val = parent.get("status", "")
    parent_cluster_count = parent.get("cluster_count_30m", 1)
    last_seen_age = parent.get("last_seen_age_sec", 0)

    # v11 — GitHub Issue sync
    issue_no = parent.get("issue_number")
    issue_url = parent.get("issue_url", "")
    child_action = child.get("action", "none")

    # v12 — Slack thread sync
    slack_channel = parent.get("slack_channel_id", "")
    slack_thread_ts = parent.get("slack_thread_ts", "")

    # v13 — source of truth lock
    mapping_source = parent.get("mapping_source", "github_issue")
    mapping_lock = parent.get("mapping_lock", "authoritative")

    md = f"""# Auto Incident Report

- Workflow: `{data.get('workflow_name', '')}`
- Run ID: `{data.get('run_id', '')}`
- Root cause: `{root}`
- Confidence: `{confidence}`
- Secondary cause: `{secondary_cause}`
- Escalation mode: `{esc_mode}`
- Severity: `{esc_sev}`
- Mention team: `{esc_team}`
- First action: `{first_cmd}`
- Ping first: `{first_owner}`
- Click first: {click_first}
- Dedupe key: `{dedupe_key}`
- Repeat count (30m): `{repeat_count}`
- Override applied: `{repeat_override}`
- Cluster key: `{cluster_key}`
- Storm control: `{storm_active}`
- Cluster count (30m): `{storm_count}`
- Parent incident: `{parent_key}`
- Parent status: `{parent_status_val}`
- Child action: `{child_action}`
- Parent issue: `#{issue_no}`
- Parent issue URL: {issue_url}
- Slack channel: `{slack_channel}`
- Slack thread_ts: `{slack_thread_ts}`
- Mapping source: `{mapping_source}`
- Mapping lock: `{mapping_lock}`

## Summary
{data.get('summary', '')}

## Escalation Decision
- If `page_oncall`: ping real oncall now
- If `channel_only`: post channel only, no pager
- If `suppress`: keep artifact/report only unless repeated

## Repeat-Incident Policy
- 1x: channel_only
- 2x / 30m: force `page_oncall`
- 3x / 30m: bump severity by 1 level

## Parent Incident Lifecycle
- opened → first clustered incident
- updated → more child incidents still arriving
- stabilized → no fresh child spike, but still inside window
- resolved → quiet long enough to close cluster
- Child incidents (30m): `{parent_cluster_count}`
- Last seen age (sec): `{last_seen_age}`

## Parent Sync
- New clustered incidents should update the same parent issue
- Do not open a new issue when `parent_incident_key` already exists

## Slack Thread Sync
- First parent incident opens root Slack message
- Child incidents reply into the same thread

## Source of Truth
- GitHub Issue marker is authoritative for parent mapping
- Slack thread creation must read issue mapping first
- Memory file is a cache only; do not treat it as lock source

## Ranked Causes
{ranked_lines}

## Evidence
{evidence_lines}

## Recommended Actions (Primary)
### Commands
{primary_cmds}

### Dashboards
{primary_dash}

### Services to Check
{primary_srv}

### Ping First
{primary_own}
"""

    if secondary_act:
        md += "\n## Secondary Actions\n" + _fmt_list(secondary_act.get("commands", []))

    if storm_active:
        md += f"\n## Storm Control\n- Parent incident mode enabled\n- Reason: `{storm_reason}`\n"

    md += f"""
## Linked Resources (Primary)
- Runbook: {runbook}

### Dashboards
{dash_lines}

### Logs
{log_lines}

### Chat / Oncall
{chat_lines}
"""

    if link_secondary:
        md += "\n## Linked Resources (Secondary)\n- Runbook: " + str(
            link_secondary.get("runbook", "")
        )

    md += f"""
## Suggested next action
{NEXT_ACTIONS.get(root, NEXT_ACTIONS['unknown'])}
"""

    Path(args.output).write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
