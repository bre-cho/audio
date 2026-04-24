#!/usr/bin/env python3
"""
sync_parent_issue.py — v13/v14

GitHub Issue = authoritative source of truth for each parent_incident_key.

Pass 1 (before Slack sync):
  - Open or find the parent issue.
  - Parse the INCIDENT_MAP marker to hydrate classification with
    slack_thread_ts / slack_channel_id / issue_mapping_version.

Pass 2 (after Slack sync, called again):
  - Write the updated slack_thread_ts back into the INCIDENT_MAP marker
    using an optimistic-lock retry loop (updated_at + version check).

Both passes share the same entry-point; behaviour is driven by whatever
the classification JSON contains at call time.
"""
import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

MAX_RETRIES = 3
RETRY_SLEEP_SEC = 2

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


def extract_issue_map(body: str) -> dict:
    """Parse the INCIDENT_MAP JSON block embedded in an issue body."""
    m = _MARKER_RE.search(body or "")
    out = json.loads(m.group(1)) if m else {}
    out["issue_mapping_version"] = int(out.get("issue_mapping_version", 0))
    return out


def merge_issue_map(old_map: dict, new_map: dict) -> dict:
    """Merge two maps: non-empty new values win; version is incremented."""
    out = dict(old_map or {})
    for k, v in (new_map or {}).items():
        if v not in (None, "", []):
            out[k] = v
    out["issue_mapping_version"] = (
        max(
            int((old_map or {}).get("issue_mapping_version", 0)),
            int((new_map or {}).get("issue_mapping_version", 0)),
        )
        + 1
    )
    return out


def build_marker_block(imap: dict) -> str:
    return f"<!-- INCIDENT_MAP\n{json.dumps(imap, indent=2)}\n-->"


def find_issue(repo: str, token: str, parent_key: str) -> dict | None:
    """Search for an existing issue by parent_incident_key in INCIDENT_MAP marker."""
    q = urllib.parse.quote(
        f'repo:{repo} "parent_incident_key": "{parent_key}" in:body is:issue'
    )
    res = _gh("GET", f"https://api.github.com/search/issues?q={q}", token)
    items = res.get("items", [])
    return items[0] if items else None


def get_issue(repo: str, token: str, number: int) -> dict:
    return _gh("GET", f"https://api.github.com/repos/{repo}/issues/{number}", token)


def lock_conflict(
    latest_issue: dict, expected_updated_at: str | None, expected_version: int
) -> bool:
    """Return True if another process has written to the issue since we read it."""
    latest_map = extract_issue_map(latest_issue.get("body", ""))
    return latest_issue.get("updated_at") != expected_updated_at or int(
        latest_map.get("issue_mapping_version", 0)
    ) > expected_version


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--classification", required=True)
    args = ap.parse_args()

    token = os.getenv("GITHUB_TOKEN", "")
    cpath = Path(args.classification)
    data = json.loads(cpath.read_text(encoding="utf-8"))

    parent = data.get("parent_incident", {})
    child = data.get("child_incident", {})
    parent_key = parent.get("parent_incident_key", "")
    status = parent.get("status", "opened")
    summary = data.get("summary", "")
    run_id = data.get("run_id", "")

    if not token or not parent_key:
        raise SystemExit("missing GITHUB_TOKEN or parent_incident_key")

    sev = data.get("escalation", {}).get("severity", "P3").lower()
    labels = ["incident", "auto-incident", f"severity:{sev}"]

    # ── find existing issue (with one race-condition retry) ─────────────────
    issue = find_issue(args.repo, token, parent_key)
    if not issue:
        issue = find_issue(args.repo, token, parent_key)

    # ── hydrate classification from authoritative INCIDENT_MAP marker ────────
    imap = extract_issue_map(issue.get("body", "")) if issue else {}
    issue_updated_at = issue.get("updated_at") if issue else None

    # Issue mapping is authoritative; pull values not yet set in this run
    for field in ("slack_thread_ts", "slack_channel_id"):
        if imap.get(field) and not parent.get(field):
            parent[field] = imap[field]
    parent["issue_mapping_version"] = imap.get("issue_mapping_version", 0)
    parent["last_issue_updated_at"] = issue_updated_at
    parent["mapping_source"] = "github_issue"
    parent["mapping_lock"] = "authoritative"

    # ── build desired INCIDENT_MAP for this run ──────────────────────────────
    desired_imap = merge_issue_map(
        imap,
        {
            "parent_incident_key": parent_key,
            "slack_thread_ts": parent.get("slack_thread_ts"),
            "slack_channel_id": parent.get("slack_channel_id"),
        },
    )

    if issue:
        parent["issue_number"] = issue["number"]
        parent["issue_url"] = issue["html_url"]

        # Post short update comment
        comment_body = (
            f"- status=`{status}` "
            f"root=`{data.get('root_cause')}` "
            f"confidence=`{data.get('confidence')}` "
            f"run=`{run_id}` "
            f"summary={summary}"
        )
        _gh("POST", issue["comments_url"], token, {"body": comment_body})
        child["action"] = "comment_existing_issue"
        if status == "resolved":
            child["action"] = "close_parent_issue"

        # ── optimistic-lock write-back of INCIDENT_MAP marker ───────────────
        expected_updated_at = issue_updated_at
        expected_version = int(imap.get("issue_mapping_version", 0))
        for attempt in range(MAX_RETRIES):
            latest = get_issue(args.repo, token, issue["number"])
            if lock_conflict(latest, expected_updated_at, expected_version):
                # Conflict detected — refresh, merge, back-off, retry
                latest_imap = extract_issue_map(latest.get("body", ""))
                desired_imap = merge_issue_map(
                    latest_imap,
                    {
                        "parent_incident_key": parent_key,
                        "slack_thread_ts": parent.get("slack_thread_ts"),
                        "slack_channel_id": parent.get("slack_channel_id"),
                    },
                )
                expected_updated_at = latest.get("updated_at")
                expected_version = int(latest_imap.get("issue_mapping_version", 0))
                time.sleep(RETRY_SLEEP_SEC)
                continue

            # No conflict — patch the issue body
            latest_body = latest.get("body", "")
            new_marker = build_marker_block(desired_imap)
            if _MARKER_RE.search(latest_body):
                new_body = _MARKER_RE.sub(new_marker, latest_body, count=1)
            else:
                new_body = new_marker + "\n" + latest_body

            patch_payload: dict = {"body": new_body}
            if status == "resolved":
                patch_payload["state"] = "closed"
            _gh(
                "PATCH",
                f"https://api.github.com/repos/{args.repo}/issues/{issue['number']}",
                token,
                patch_payload,
            )
            parent["issue_mapping_version"] = desired_imap["issue_mapping_version"]
            break
        else:
            print(
                f"Warning: could not acquire optimistic lock after {MAX_RETRIES} retries;"
                " skipping marker update"
            )
    else:
        # Create new issue with INCIDENT_MAP marker embedded in body
        marker_block = build_marker_block(desired_imap)
        full_body = f"""{marker_block}

## Parent Incident
- Key: `{parent_key}`
- Status: `{status}`
- Root cause: `{data.get("root_cause")}`
- Confidence: `{data.get("confidence")}`
- Secondary cause: `{data.get("secondary_cause")}`
- Latest summary: {summary}
"""
        created = _gh(
            "POST",
            f"https://api.github.com/repos/{args.repo}/issues",
            token,
            {
                "title": f"[auto-incident] {parent_key}",
                "body": full_body,
                "labels": labels,
            },
        )
        parent["issue_number"] = created["number"]
        parent["issue_url"] = created["html_url"]
        parent["issue_mapping_version"] = desired_imap["issue_mapping_version"]
        child["action"] = "open_parent_issue"

    data["parent_incident"] = parent
    data["child_incident"] = child
    cpath.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(data["parent_incident"], indent=2))


if __name__ == "__main__":
    main()
