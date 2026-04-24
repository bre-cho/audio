#!/usr/bin/env python3
"""
sync_parent_slack_thread.py — v12/v13

Slack thread mapping is driven by the authoritative INCIDENT_MAP in the
GitHub Issue (hydrated into classification by sync_parent_issue.py).

- If slack_thread_ts already exists in classification (from issue map):
    reply into the existing thread  (action = reuse_issue_mapped_thread)
- If issue_url exists but no thread_ts yet:
    wait — do not open a duplicate root message  (action = await_issue_lock_refresh)
- If neither issue nor thread_ts:
    open root Slack message and save thread_ts  (action = open_parent_thread)
"""
import argparse
import json
import os
import urllib.request
from pathlib import Path


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _slack(method: str, token: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"https://slack.com/api/{method}",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read().decode()
        return json.loads(raw) if raw else {}


def _slack_checked(method: str, token: str, payload: dict) -> dict:
    res = _slack(method, token, payload)
    if not res.get("ok"):
        raise SystemExit(f"Slack API error ({method}): {res.get('error', 'unknown')}")
    return res


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--classification", required=True)
    args = ap.parse_args()

    token = os.getenv("SLACK_BOT_TOKEN", "")
    channel = os.getenv("SLACK_CHANNEL_ID", "")
    cpath = Path(args.classification)
    data = json.loads(cpath.read_text(encoding="utf-8"))

    parent = data.get("parent_incident", {})
    child = data.get("child_incident", {})
    key = parent.get("parent_incident_key", "")
    status = parent.get("status", "opened")
    summary = data.get("summary", "")
    issue_url = parent.get("issue_url", "")
    run_id = data.get("run_id", "")

    if not token or not channel or not key:
        raise SystemExit("missing SLACK_BOT_TOKEN, SLACK_CHANNEL_ID, or parent_incident_key")

    # thread_ts is hydrated from the authoritative issue mapping
    thread_ts = parent.get("slack_thread_ts")
    # use channel from issue mapping if env var not provided
    effective_channel = channel or parent.get("slack_channel_id", "")

    if thread_ts:
        # Reuse the issue-mapped Slack thread
        msg = (
            f"↪️ update | parent=`{key}` | status=`{status}` "
            f"| run=`{run_id}` | summary={summary}"
        )
        _slack_checked(
            "chat.postMessage",
            token,
            {"channel": effective_channel, "thread_ts": thread_ts, "text": msg},
        )
        child["action"] = "reuse_issue_mapped_thread"
    elif parent.get("issue_url"):
        # Issue exists but thread_ts not yet in mapping — wait for lock refresh.
        # Exit 0 so the workflow step succeeds; the next run will pick up the mapping.
        child["action"] = "await_issue_lock_refresh"
        data["child_incident"] = child
        cpath.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(json.dumps({"thread_ts": None, "action": "await_issue_lock_refresh"}, indent=2))
        print("Info: issue exists but slack_thread_ts not yet mapped; skipping Slack post.")
        raise SystemExit(0)
    else:
        # No issue yet — open root Slack message for this parent
        msg = (
            f"🚨 Parent Incident\n"
            f"key=`{key}`\n"
            f"status=`{status}`\n"
            f"root=`{data.get('root_cause')}` conf=`{data.get('confidence')}`\n"
            f"issue={issue_url}\n"
            f"summary={summary}"
        )
        res = _slack_checked("chat.postMessage", token, {"channel": effective_channel, "text": msg})
        parent["slack_channel_id"] = effective_channel
        parent["slack_thread_ts"] = res.get("ts")
        child["action"] = "open_parent_thread"

    data["parent_incident"] = parent
    data["child_incident"] = child
    cpath.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {"thread_ts": parent.get("slack_thread_ts"), "action": child.get("action")},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
