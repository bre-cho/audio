#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path


def load_json(p):
    return json.loads(Path(p).read_text()) if Path(p).exists() else {}


def save_json(p, d):
    Path(p).write_text(json.dumps(d, indent=2))


def fingerprint(root, secondary):
    return hashlib.sha1(f"{root}:{secondary}".encode()).hexdigest()[:12]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classification", required=True)
    ap.add_argument("--postmortem", required=True)
    args = ap.parse_args()

    data = load_json(args.classification)
    kb = load_json(".incident_knowledge.json")

    root = data.get("root_cause")
    sec = data.get("secondary_cause")
    actions = data.get("recommended_actions", {}).get("primary", {})
    fp = fingerprint(root, sec)

    entry = {
        "fingerprint": fp,
        "root_cause": root,
        "secondary_cause": sec,
        "commands": actions.get("commands", []),
        "services": actions.get("services", []),
        "workflow": data.get("workflow_name"),
        "severity": data.get("escalation", {}).get("severity"),
        "count": 1,
    }

    # Apply slight decay to all existing pattern counts before inserting new one
    for p in kb.get("patterns", []):
        p["count"] = round(p["count"] * 0.99, 4)

    existing = next((x for x in kb.get("patterns", []) if x["fingerprint"] == fp), None)
    if existing:
        existing["count"] += 1
        # Merge commands without duplicates
        existing["commands"] = list(dict.fromkeys(existing["commands"] + entry["commands"]))
    else:
        kb.setdefault("patterns", []).append(entry)

    save_json(".incident_knowledge.json", kb)

    # Generate regression test seed (markdown)
    test_md = f"""# Regression Test Seed

## Case: {root}
- secondary: {sec}
- expected: classifier → {root}
- commands:
{chr(10).join('- ' + c for c in entry['commands'])}
"""
    Path("regression_tests_seed.md").write_text(test_md)

    # Generate regression test seed (JSON)
    test_json = {
        "input": {"root_cause": root},
        "expected": {"classification": root},
    }
    Path("regression_tests_seed.json").write_text(json.dumps(test_json, indent=2))

    data["knowledge_memory"] = {
        "fingerprint": fp,
        "pattern_count": len(kb.get("patterns", [])),
    }
    save_json(args.classification, data)
    print(json.dumps(data["knowledge_memory"], indent=2))


if __name__ == "__main__":
    main()
