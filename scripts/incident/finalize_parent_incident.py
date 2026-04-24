#!/usr/bin/env python3
import argparse, json, os, urllib.request
from datetime import datetime, timezone
from pathlib import Path


def gh(method, url, token, payload=None):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read().decode()
        return json.loads(raw) if raw else {}


def slack(method, token, payload):
    req = urllib.request.Request(
        f"https://slack.com/api/{method}",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--classification", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    token = os.getenv("GITHUB_TOKEN")
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    data = json.loads(Path(args.classification).read_text(encoding="utf-8"))

    # Idempotency guard — skip if already finalized
    if data.get("finalizer", {}).get("status") == "finalized":
        print("already finalized; skip")
        return

    parent = data.get("parent_incident", {})
    status = parent.get("status")
    issue_no = parent.get("issue_number")
    channel = parent.get("slack_channel_id")
    thread_ts = parent.get("slack_thread_ts")

    if status != "resolved":
        print("parent not resolved; skip finalizer")
        return

    postmortem = render_postmortem(data)
    Path(args.output).write_text(postmortem, encoding="utf-8")

    final_comment = f"## ✅ Incident Finalized\n\n{postmortem}"
    if token and issue_no:
        gh("POST", f"https://api.github.com/repos/{args.repo}/issues/{issue_no}/comments",
           token, {"body": final_comment})
        if os.getenv("AUTO_CLOSE_PARENT_ISSUE", "0") == "1":
            gh("PATCH", f"https://api.github.com/repos/{args.repo}/issues/{issue_no}",
               token, {"state": "closed"})

    if slack_token and channel and thread_ts:
        slack("chat.postMessage", slack_token, {
            "channel": channel,
            "thread_ts": thread_ts,
            "text": (
                f"✅ Parent incident resolved.\nPostmortem seed generated.\n"
                f"root={data.get('root_cause')} confidence={data.get('confidence')}"
            ),
        })

    data["finalizer"] = {
        "status": "finalized",
        "postmortem_seed": args.output,
        "closed_at": datetime.now(timezone.utc).isoformat(),
    }
    Path(args.classification).write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(data["finalizer"], indent=2))


def render_postmortem(data):
    parent = data.get("parent_incident", {})
    repeat = data.get("repeat_incident", {})
    storm = data.get("storm_control", {})
    actions = data.get("recommended_actions", {}).get("primary", {})
    evidence = data.get("evidence", [])

    # Timeline — use explicit timeline list if present, else derive from parent fields
    timeline_items = data.get("timeline", [])
    if not timeline_items:
        timeline_items = [
            f"status={parent.get('status')}",
            f"child incidents in 30m: {parent.get('cluster_count_30m')}",
            f"repeat count 30m: {repeat.get('repeat_count_30m')}",
            f"storm active: {storm.get('active')}",
        ]
    timeline_lines = "\n".join(f"- {x}" for x in timeline_items)

    evidence_lines = "\n".join(f"- {x}" for x in evidence) or "- No evidence captured"
    action_lines = "\n".join(f"- {x}" for x in actions.get("commands", [])) or "- No action captured"

    # Follow-up owners
    owners = actions.get("owners", []) or data.get("escalation", {}).get("mention_team", "oncall")
    # owners may be a list (from action map) or a plain string (from escalation mention_team)
    if isinstance(owners, (list, tuple)):
        owner_lines = "\n".join(f"- {x}" for x in owners)
    else:
        owner_lines = f"- {owners}"

    followups = "\n".join(f"- {x}" for x in actions.get("services", [])) or "- Define follow-up owner"

    return f"""# Postmortem Seed

## Summary
Parent incident `{parent.get("parent_incident_key")}` resolved.

## Timeline
{timeline_lines}

## Root Cause
- Primary: `{data.get("root_cause")}`
- Confidence: `{data.get("confidence")}`
- Secondary: `{data.get("secondary_cause")}`

## Impact
- Workflow: `{data.get("workflow_name")}`
- Severity: `{data.get("escalation", {}).get("severity")}`
- Escalation mode: `{data.get("escalation", {}).get("mode")}`

## Evidence
{evidence_lines}

## Actions Taken
{action_lines}

## Follow-up Owners
{owner_lines}

## Follow-ups
{followups}

## Links
- Parent issue: {parent.get("issue_url")}
- Slack thread_ts: `{parent.get("slack_thread_ts")}`
"""


if __name__ == "__main__":
    main()
