#!/usr/bin/env python3
"""
sync_parent_slack_thread.py — v12

For a given parent_incident_key:
- If no slack_thread_ts yet: post root message, save thread_ts
- Else: reply into existing thread with a short child update
- If the current incident is a child but parent has no thread_ts yet
  (and issue already exists), wait rather than opening a duplicate thread.
- Writes slack_channel_id / slack_thread_ts back into classification JSON.
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

    thread_ts = parent.get("slack_thread_ts")

    # Race-condition guard: if this is a child incident, the parent issue already
    # exists but thread hasn't been written yet — wait rather than opening a new root.
    if not thread_ts and child.get("is_child") and parent.get("issue_url"):
        child["action"] = "await_parent_thread"
        data["child_incident"] = child
        cpath.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(json.dumps({"thread_ts": None, "action": "await_parent_thread"}, indent=2))
        raise SystemExit(0)

    if not thread_ts:
        # Open root message for this parent
        msg = (
            f"🚨 Parent Incident\n"
            f"key=`{key}`\n"
            f"status=`{status}`\n"
            f"root=`{data.get('root_cause')}` conf=`{data.get('confidence')}`\n"
            f"issue={issue_url}\n"
            f"summary={summary}"
        )
        res = _slack_checked("chat.postMessage", token, {"channel": channel, "text": msg})
        parent["slack_channel_id"] = channel
        parent["slack_thread_ts"] = res.get("ts")
        child["action"] = "open_parent_thread"
    else:
        # Short child reply to keep thread readable
        msg = (
            f"↪️ update | parent=`{key}` | status=`{status}` "
            f"| run=`{run_id}` | summary={summary}"
        )
        _slack_checked(
            "chat.postMessage",
            token,
            {"channel": channel, "thread_ts": thread_ts, "text": msg},
        )
        child["action"] = "reply_parent_thread"

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
