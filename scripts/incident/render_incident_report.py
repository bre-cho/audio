#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

NEXT_ACTIONS = {
    "provider_failure": "- Kiem tra trang thai provider / quota API upstream / chinh sach retry.",
    "queue_backlog": "- Kiem tra suc khoe worker Celery, do tre Redis, do sau hang doi, job bi ket.",
    "ffmpeg_failure": "- Kiem tra tinh toan ven file media dau vao, xu ly codec, tham so lenh ffmpeg.",
    "infra_down": "- Kiem tra suc khoe container/node/network/storage.",
    "test_regression": "- Kiem tra diff code moi nhat va cac assertion dang loi.",
    "unknown": "- Chua tim thay tin hieu manh. Kiem tra log workflow thu cong.",
}


def _fmt_list(items):
    return "\n".join(f"- {x}" for x in items) if items else "_khong_co_"


def _fmt_dict(d):
    return "\n".join(f"- {k}: {v}" for k, v in d.items()) if d else "_khong_co_"


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
    first_cmd = (primary_act.get("commands") or ["kiem tra log"])[0]
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
    esc_mode = esc.get("mode", "chi_kenh")
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
    child_action = child.get("action", "khong")

    # v12 — Slack thread sync
    slack_channel = parent.get("slack_channel_id", "")
    slack_thread_ts = parent.get("slack_thread_ts", "")

    # v13 — source of truth lock
    mapping_source = parent.get("mapping_source", "github_issue")
    mapping_lock = parent.get("mapping_lock", "authoritative")

    # v17 — finalizer
    finalizer = data.get("finalizer", {})
    finalizer_status = finalizer.get("status", "not_finalized")
    postmortem_seed = finalizer.get("postmortem_seed")

    # v18 — knowledge memory
    km = data.get("knowledge_memory", {})
    km_fp = km.get("fingerprint")
    km_count = km.get("pattern_count")

    # v16 — drift detector
    recon = data.get("state_reconciler", {})
    drift = recon.get("drift", {})
    drift_level = drift.get("level", "khong")
    drift_action = drift.get("action", "khong")
    drift_reason = drift.get("reason", "")
    drift_corruption = drift.get("corruption_type", "")

    md = f"""# Bao Cao Su Co Tu Dong

- Workflow: `{data.get('workflow_name', '')}`
- Run ID: `{data.get('run_id', '')}`
- Nguyen nhan goc: `{root}`
- Do tin cay: `{confidence}`
- Nguyen nhan phu: `{secondary_cause}`
- Che do nang cap: `{esc_mode}`
- Muc do: `{esc_sev}`
- Nhom duoc nhac den: `{esc_team}`
- Hanh dong dau tien: `{first_cmd}`
- Nguoi ping dau tien: `{first_owner}`
- Duong dan uu tien: {click_first}
- Khoa chong trung lap: `{dedupe_key}`
- So lan lap lai (30p): `{repeat_count}`
- Da ap dung ghi de: `{repeat_override}`
- Khoa cum su co: `{cluster_key}`
- Trang thai storm control: `{storm_active}`
- So su co trong cum (30p): `{storm_count}`
- Su co cha: `{parent_key}`
- Trang thai su co cha: `{parent_status_val}`
- Hanh dong su co con: `{child_action}`
- Issue cha: `#{issue_no}`
- URL issue cha: {issue_url}
- Kenh Slack: `{slack_channel}`
- Slack thread_ts: `{slack_thread_ts}`
- Nguon anh xa: `{mapping_source}`
- Khoa anh xa: `{mapping_lock}`
- Muc do drift: `{drift_level}`
- Hanh dong drift: `{drift_action}`
- Ly do drift: `{drift_reason}`

## Tom Tat
{data.get('summary', '')}

## Quyet Dinh Nang Cap
- Neu `page_oncall`: ping oncall that ngay
- Neu `channel_only`: chi gui vao kenh, khong goi pager
- Neu `suppress`: chi luu artifact/bao cao neu chua lap lai

## Chinh Sach Su Co Lap Lai
- 1 lan: channel_only
- 2 lan / 30p: bat buoc `page_oncall`
- 3 lan / 30p: tang muc do len 1 cap

## Vong Doi Su Co Cha
- opened → su co dau tien trong cum
- updated → tiep tuc co su co con moi
- stabilized → khong con dot tang moi, nhung van trong cua so theo doi
- resolved → yen lang du lau de dong cum su co
- Su co con (30p): `{parent_cluster_count}`
- Thoi gian lan cuoi xuat hien (giay): `{last_seen_age}`

## Dong Bo Su Co Cha
- Su co con trong cung cum phai cap nhat cung mot issue cha
- Khong mo issue moi khi `parent_incident_key` da ton tai

## Dong Bo Chuoi Slack
- Su co cha dau tien tao tin nhan goc tren Slack
- Cac su co con tra loi trong cung mot thread

## Nguon Su That
- Marker GitHub Issue la nguon quyen uy de anh xa su co cha
- Tao thread Slack phai doc anh xa tu issue truoc
- File memory chi la cache, khong duoc xem la nguon khoa

## Chinh Sach Drift
- `safe_auto_fix` → da sua tu dong, khong can thao tac them
- `needs_retry` → loi lookup ben ngoai tam thoi; thu lai buoc dong bo/reconcile
- `needs_human_review` → sai lech trang thai da nguon; nang cap cho SRE

## Xep Hang Nguyen Nhan
{ranked_lines}

## Bang Chung
{evidence_lines}

## Hanh Dong De Xuat (Chinh)
### Lenh
{primary_cmds}

### Dashboard
{primary_dash}

### Dich Vu Can Kiem Tra
{primary_srv}

### Nguoi Can Ping Dau Tien
{primary_own}
"""

    if secondary_act:
        md += "\n## Hanh Dong Phu\n" + _fmt_list(secondary_act.get("commands", []))

    if storm_active:
        md += f"\n## Storm Control\n- Da bat che do su co cha\n- Ly do: `{storm_reason}`\n"

    if drift_corruption:
        md += f"\n## Sai Lech Trang Thai\n- Loai sai lech: `{drift_corruption}`\n"

    md += f"""
## Tai Nguyen Lien Ket (Chinh)
- Runbook: {runbook}

### Dashboard
{dash_lines}

### Log
{log_lines}

### Kenh Chat / Oncall
{chat_lines}
"""

    if link_secondary:
        md += "\n## Tai Nguyen Lien Ket (Phu)\n- Runbook: " + str(
            link_secondary.get("runbook", "")
        )

    md += f"""
## Goi Y Hanh Dong Tiep Theo
{NEXT_ACTIONS.get(root, NEXT_ACTIONS['unknown'])}

## Finalizer
- Trang thai: `{finalizer_status}`
- Mam postmortem: `{postmortem_seed}`

## Bo Nho Tri Thuc
- Dau van tay mau: `{km_fp}`
- Tong so mau da luu: `{km_count}`
"""

    if parent.get("status") == "resolved":
        md += "\n## Ban Giao Dong Su Co\n- Su co cha da duoc resolve\n- Can xem lai mam postmortem truoc khi luu tru\n"

    Path(args.output).write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
