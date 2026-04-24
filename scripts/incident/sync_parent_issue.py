#!/usr/bin/env python3
"""
sync_parent_issue.py — v11

For a given parent_incident_key:
- If a GitHub Issue already exists: comment an update (short body for child)
- Else: open a new Issue with labels including severity
- If status == resolved: close the issue
- Writes issue_number / issue_url back into classification JSON.
"""
import argparse
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


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


def find_issue(repo: str, token: str, parent_key: str) -> dict | None:
    """Search for an existing issue that contains the stable marker."""
    marker = f"<!-- incident:{parent_key} -->"
    q = urllib.parse.quote(f'repo:{repo} "{marker}" in:body is:issue')
    res = _gh("GET", f"https://api.github.com/search/issues?q={q}", token)
    items = res.get("items", [])
    return items[0] if items else None


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
    marker = f"<!-- incident:{parent_key} -->"

    issue = find_issue(args.repo, token, parent_key)

    if issue:
        # Short child-update comment to keep thread clean
        body = (
            f"- status=`{status}` "
            f"root=`{data.get('root_cause')}` "
            f"confidence=`{data.get('confidence')}` "
            f"run=`{run_id}` "
            f"summary={summary}"
        )
        _gh("POST", issue["comments_url"], token, {"body": body})
        parent["issue_number"] = issue["number"]
        parent["issue_url"] = issue["html_url"]
        child["action"] = "comment_existing_issue"

        if status == "resolved":
            _gh(
                "PATCH",
                f"https://api.github.com/repos/{args.repo}/issues/{issue['number']}",
                token,
                {"state": "closed"},
            )
            child["action"] = "close_parent_issue"
    else:
        # Race-condition guard: re-search once more before creating
        issue = find_issue(args.repo, token, parent_key)
        if issue:
            body = (
                f"- status=`{status}` "
                f"root=`{data.get('root_cause')}` "
                f"confidence=`{data.get('confidence')}` "
                f"run=`{run_id}` "
                f"summary={summary}"
            )
            _gh("POST", issue["comments_url"], token, {"body": body})
            parent["issue_number"] = issue["number"]
            parent["issue_url"] = issue["html_url"]
            child["action"] = "comment_existing_issue"
        else:
            full_body = f"""{marker}

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
            child["action"] = "open_parent_issue"

    data["parent_incident"] = parent
    data["child_incident"] = child
    cpath.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(data["parent_incident"], indent=2))


if __name__ == "__main__":
    main()
