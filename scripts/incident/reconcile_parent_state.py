#!/usr/bin/env python3
"""
reconcile_parent_state.py — v16

STATE RECONCILER + DRIFT DETECTOR: aligns three sources of truth into one
consistent state, then classifies any remaining drift and drives the repair
policy (auto-fix / retry / escalate).

Priority order (highest → lowest):
  1. GitHub Issue INCIDENT_MAP marker  — authoritative
  2. Slack thread (external synced object)
  3. Classification JSON               — working copy

Drift levels:
  - none              → all sources already aligned
  - safe_auto_fix     → repaired automatically; no further action needed
  - needs_retry       → transient external lookup failure; retry sync
  - needs_human_review→ multi-source state corruption; escalate
"""
import argparse
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

_MARKER_RE = re.compile(r"<!-- INCIDENT_MAP\n(\{.*?\})\n-->", re.DOTALL)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _gh(method: str, url: str, token: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.request.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise SystemExit(f"GitHub API error {exc.code} {method} {url}: {body}") from exc


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
        return json.loads(r.read().decode())


def extract_issue_map(body: str) -> dict:
    m = _MARKER_RE.search(body or "")
    out = json.loads(m.group(1)) if m else {}
    out["issue_mapping_version"] = int(out.get("issue_mapping_version", 0))
    return out


def build_marker_block(imap: dict) -> str:
    return f"<!-- INCIDENT_MAP\n{json.dumps(imap, indent=2)}\n-->"


def find_issue(repo: str, token: str, parent_key: str) -> dict | None:
    q = urllib.parse.quote(
        f'repo:{repo} "parent_incident_key": "{parent_key}" in:body is:issue'
    )
    res = _gh("GET", f"https://api.github.com/search/issues?q={q}", token)
    items = res.get("items", [])
    return items[0] if items else None


def verify_slack_thread(token: str, channel: str, thread_ts: str) -> bool:
    """Return True if the Slack thread is accessible (replies endpoint succeeds)."""
    if not token or not channel or not thread_ts:
        return False
    try:
        res = _slack(
            "conversations.replies",
            token,
            {"channel": channel, "ts": thread_ts, "limit": 1},
        )
        return bool(res.get("ok"))
    except Exception as exc:
        print(f"Warning: Slack thread verification failed for ts={thread_ts}: {exc}")
        return False


# ---------------------------------------------------------------------------
# drift classifier
# ---------------------------------------------------------------------------

_TRANSIENT_CONFLICTS = {"slack_thread_lookup_failed", "slack_thread_unreadable"}


def classify_drift(conflicts: list, changed: list) -> dict:
    """Return drift level, action, and reason given reconciliation results."""
    conflict_set = set(conflicts)
    if not conflicts:
        if changed:
            return {
                "level": "safe_auto_fix",
                "action": "auto_repaired",
                "reason": "state_aligned_to_issue",
            }
        return {"level": "none", "action": "none", "reason": ""}

    if conflict_set <= _TRANSIENT_CONFLICTS:
        return {"level": "needs_retry", "action": "retry_sync", "reason": "transient_external_lookup"}

    if "multi_source_state_corruption" in conflict_set:
        return {
            "level": "needs_human_review",
            "action": "escalate_corruption",
            "reason": "state_diverged",
            "corruption_type": "cross-system-parent-mapping-divergence",
        }

    if any(
        "issue.marker<-json.slack_mapping" in x or "json.slack_thread_ts<-issue" in x
        for x in changed
    ):
        return {
            "level": "safe_auto_fix",
            "action": "auto_repaired",
            "reason": "mapping_repaired",
        }

    return {"level": "needs_human_review", "action": "escalate_corruption", "reason": "state_diverged"}


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--classification", required=True)
    args = ap.parse_args()

    gtoken = os.getenv("GITHUB_TOKEN", "")
    stoken = os.getenv("SLACK_BOT_TOKEN", "")
    cpath = Path(args.classification)
    data = json.loads(cpath.read_text(encoding="utf-8"))

    parent = data.get("parent_incident", {})
    child = data.get("child_incident", {})
    parent_key = parent.get("parent_incident_key", "")

    reconciled: dict = {
        "source": "github_issue",
        "changed": [],
        "conflicts": [],
    }

    if not gtoken or not parent_key:
        print(json.dumps({"skipped": True, "reason": "no GITHUB_TOKEN or parent_incident_key"}))
        return

    # ── 1. Fetch authoritative state from GitHub Issue ───────────────────────
    issue = find_issue(args.repo, gtoken, parent_key)
    imap = extract_issue_map(issue.get("body", "")) if issue else {}

    # Ensure issue reference is in the classification
    if issue:
        if not parent.get("issue_number"):
            parent["issue_number"] = issue["number"]
            reconciled["changed"].append("json.issue_number<-issue")
        if not parent.get("issue_url"):
            parent["issue_url"] = issue["html_url"]
            reconciled["changed"].append("json.issue_url<-issue")

    issue_thread = imap.get("slack_thread_ts")
    issue_channel = imap.get("slack_channel_id")
    json_thread = parent.get("slack_thread_ts")
    json_channel = parent.get("slack_channel_id")

    # ── 2. Detect heavy mismatches (before repair) ───────────────────────────
    if issue and parent.get("issue_url") and parent.get("issue_url") != issue.get("html_url"):
        reconciled["conflicts"].append("issue_url_mismatch")

    if issue_thread and json_thread and issue_thread != json_thread:
        reconciled["conflicts"].append("slack_thread_ts_mismatch")

    if (
        "issue_url_mismatch" in reconciled["conflicts"]
        and "slack_thread_ts_mismatch" in reconciled["conflicts"]
    ):
        reconciled["conflicts"].append("multi_source_state_corruption")

    # ── 3. Reconcile JSON ← Issue (issue wins on conflict) ───────────────────
    if issue_thread and json_thread and json_thread != issue_thread:
        parent["slack_thread_ts"] = issue_thread
        reconciled["changed"].append("json.slack_thread_ts<-issue")

    if issue_thread and not json_thread:
        parent["slack_thread_ts"] = issue_thread
        reconciled["changed"].append("json.slack_thread_ts<-issue")

    if issue_channel and json_channel and json_channel != issue_channel:
        parent["slack_channel_id"] = issue_channel
        reconciled["changed"].append("json.slack_channel_id<-issue")

    if issue_channel and not json_channel:
        parent["slack_channel_id"] = issue_channel
        reconciled["changed"].append("json.slack_channel_id<-issue")

    # ── 4. Reconcile Issue ← JSON (write-back when issue marker is missing) ──
    if not issue_thread and json_thread and issue and gtoken:
        thread_ok = verify_slack_thread(stoken, json_channel or "", json_thread)
        if thread_ok or not stoken:
            imap["slack_thread_ts"] = json_thread
            imap["slack_channel_id"] = json_channel
            imap["issue_mapping_version"] = imap.get("issue_mapping_version", 0) + 1
            new_marker = build_marker_block(imap)
            body = issue.get("body", "")
            if _MARKER_RE.search(body):
                new_body = _MARKER_RE.sub(new_marker, body, count=1)
            else:
                new_body = new_marker + "\n" + body
            _gh(
                "PATCH",
                f"https://api.github.com/repos/{args.repo}/issues/{issue['number']}",
                gtoken,
                {"body": new_body},
            )
            reconciled["changed"].append("issue.marker<-json.slack_mapping")
        else:
            reconciled["conflicts"].append("slack_thread_lookup_failed")

    # ── 5. Classify drift ────────────────────────────────────────────────────
    drift = classify_drift(reconciled["conflicts"], reconciled["changed"])
    reconciled["drift"] = drift
    reconciled["retry_once"] = 1 if drift["level"] == "needs_retry" else 0

    # Determine reconciliation status
    if not reconciled["conflicts"] and reconciled["changed"]:
        reconciled["status"] = "healed"
    elif not reconciled["conflicts"] and not reconciled["changed"]:
        reconciled["status"] = "aligned"
    else:
        reconciled["status"] = "conflict"

    # ── 6. Apply policy side-effects ─────────────────────────────────────────
    if drift["level"] == "needs_human_review":
        esc = data.setdefault("escalation", {})
        current_sev = esc.get("severity", "P2")
        if current_sev == "P2":
            esc["severity"] = "P1"
        esc["mention_team"] = "sre"
        if "corruption_type" in drift:
            reconciled["drift"]["corruption_type"] = drift["corruption_type"]

    # ── 7. Stamp reconciliation metadata ─────────────────────────────────────
    parent["mapping_source"] = "github_issue"
    parent["mapping_lock"] = "authoritative"
    parent["reconcile_changed"] = reconciled["changed"]
    parent["reconcile_conflicts"] = reconciled["conflicts"]

    data["parent_incident"] = parent
    data["child_incident"] = child
    data["state_reconciler"] = reconciled
    cpath.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(reconciled, indent=2))


if __name__ == "__main__":
    main()
