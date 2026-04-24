#!/usr/bin/env python3
"""
apply_repeat_incident_policy.py

v8 — Repeat-incident memory + escalation override
v9 — Incident clustering + storm control
v10 — Parent incident lifecycle
"""
import argparse
import json
import time
from pathlib import Path

WINDOW_SEC = 30 * 60
SEV_ORDER = {"P3": 1, "P2": 2, "P1": 3}
CLUSTERABLE_ROOTS = {"provider_failure", "infra_down", "queue_backlog"}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def bump_severity(sev: str) -> str:
    return "P1" if sev == "P2" else ("P2" if sev == "P3" else "P1")


def workflow_family(name: str) -> str:
    name = name or ""
    if "chaos" in name:
        return "audio-chaos"
    if "e2e" in name:
        return "audio-ci"
    if "canary" in name:
        return "audio-deploy"
    return "audio-other"


def parent_status(cluster_count: int, last_seen_age_sec: int) -> str:
    if cluster_count <= 1:
        return "opened"
    if last_seen_age_sec <= 10 * 60:
        return "updated"
    if last_seen_age_sec <= 20 * 60:
        return "stabilized"
    return "resolved"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--classification", required=True)
    ap.add_argument("--memory", required=True)
    args = ap.parse_args()

    cpath = Path(args.classification)
    mpath = Path(args.memory)

    data = json.loads(cpath.read_text(encoding="utf-8"))
    now = int(time.time())
    mem: dict = (
        json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}
    )
    mem.setdefault("events", [])
    mem.setdefault("parents", [])

    # ------------------------------------------------------------------
    # v8 — repeat-incident override
    # ------------------------------------------------------------------
    key = data.get("dedupe_key", "")
    # Prune stale events
    events = [e for e in mem["events"] if now - e.get("ts", 0) <= WINDOW_SEC]
    same = [e for e in events if e.get("dedupe_key") == key]
    repeat_count = len(same) + 1

    esc = data.get("escalation", {})
    mode = esc.get("mode", "channel_only")
    sev = esc.get("severity", "P3")
    original_mode = mode

    # Override escalation based on repeat count
    if repeat_count == 1 and mode == "suppress":
        mode = "channel_only"
    if repeat_count >= 2:
        mode = "page_oncall"
    if repeat_count >= 3 and not any(
        e.get("severity") == bump_severity(sev) for e in same
    ):
        sev = bump_severity(sev)

    # Canary-deploy hard override
    wf = data.get("workflow_name", "")
    if wf == "audio-canary-deploy" and repeat_count >= 2:
        mode = "page_oncall"
        if data.get("escalation", {}).get("severity") == "P2":
            sev = "P1"

    data["repeat_incident"] = {
        "repeat_count_30m": repeat_count,
        "window_sec": WINDOW_SEC,
        "override_applied": repeat_count >= 2 or (
            repeat_count == 1 and original_mode == "suppress"
        ),
    }
    data["escalation"]["mode"] = mode
    data["escalation"]["severity"] = sev

    # ------------------------------------------------------------------
    # v9 — clustering + storm control
    # ------------------------------------------------------------------
    cluster_key = f'{data.get("root_cause")}::{workflow_family(wf)}'
    data["cluster_key"] = cluster_key

    same_cluster = [e for e in events if e.get("cluster_key") == cluster_key]
    cluster_count = len(same_cluster) + 1

    storm_active = (
        cluster_count >= 3 and data.get("root_cause") in CLUSTERABLE_ROOTS
    )
    if storm_active:
        # Collapse cluster to channel_only; pager suppressed
        data["escalation"]["mode"] = "channel_only"
        data["storm_control"] = {
            "active": True,
            "cluster_count_30m": cluster_count,
            "reason": (
                f'{data.get("root_cause")} cluster collapsed to parent incident'
            ),
        }
    else:
        data["storm_control"] = {
            "active": False,
            "cluster_count_30m": cluster_count,
            "reason": None,
        }

    # ------------------------------------------------------------------
    # v10 — parent incident lifecycle
    # ------------------------------------------------------------------
    parent_key = f'{cluster_key}::window_{now // WINDOW_SEC}'
    last_seen_ts = max(
        (e.get("ts", now) for e in same_cluster), default=now
    )
    last_seen_age_sec = max(0, now - last_seen_ts)
    p_status = parent_status(cluster_count, last_seen_age_sec)

    parent_state = {
        "parent_incident_key": parent_key,
        "status": p_status,
        "cluster_count_30m": cluster_count,
        "last_seen_age_sec": last_seen_age_sec,
    }
    data["parent_incident"] = parent_state

    is_child = cluster_count > 1
    child_info: dict = {
        "is_child": is_child,
        "linked_parent": parent_key if is_child else None,
    }
    if storm_active:
        # Determine whether first post for this parent already happened
        existing_parent = any(
            p.get("parent_incident_key") == parent_key
            for p in mem["parents"]
        )
        if existing_parent:
            data["escalation"]["mode"] = "suppress"
            child_info["action"] = "update_parent"
        else:
            child_info["action"] = "open_parent"
    else:
        child_info["action"] = "none"
    data["child_incident"] = child_info

    # ------------------------------------------------------------------
    # Persist memory
    # ------------------------------------------------------------------
    events.append({
        "dedupe_key": key,
        "cluster_key": cluster_key,
        "ts": now,
        "severity": sev,
        "mode": data["escalation"]["mode"],
        "workflow_name": wf,
        "root_cause": data.get("root_cause"),
    })
    mem["events"] = [e for e in events if now - e.get("ts", 0) <= WINDOW_SEC][-200:]

    mem["parents"] = [
        p for p in mem["parents"]
        if now - p.get("updated_ts", now) <= WINDOW_SEC
        and p.get("parent_incident_key") != parent_key
    ]
    mem["parents"].append({**parent_state, "updated_ts": now})

    cpath.write_text(json.dumps(data, indent=2), encoding="utf-8")
    mpath.write_text(json.dumps(mem, indent=2), encoding="utf-8")

    summary = {
        "repeat_incident": data["repeat_incident"],
        "storm_control": data["storm_control"],
        "parent_incident": data["parent_incident"],
        "child_incident": data["child_incident"],
        "escalation": data["escalation"],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
