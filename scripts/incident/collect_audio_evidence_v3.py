#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path


def gh_json(url, token):
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def get_failed_steps(repo, run_id, token):
    jobs = gh_json(
        f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/jobs?per_page=100",
        token,
    )
    out = {"job_conclusion_map": {}, "failed_step_names": []}
    for job in jobs.get("jobs", []):
        out["job_conclusion_map"][job["name"]] = job.get("conclusion")
        for step in job.get("steps", []):
            if step.get("conclusion") == "failure":
                out["failed_step_names"].append(
                    f'{job["name"]} :: {step.get("name", "unknown")}'
                )
    return out


LOG_TAIL_SIZE = 4000


def provider_health():
    files = []
    for base in [Path("logs"), Path("artifacts"), Path(".incident_report"), Path(".")]:
        if base.exists():
            files.extend(base.rglob("*"))
    blob = ""
    for f in files:
        if f.is_file() and f.suffix.lower() in {".log", ".txt", ".out", ".json"}:
            try:
                blob += "\n" + f.read_text(encoding="utf-8", errors="ignore")[-LOG_TAIL_SIZE:]
            except Exception:
                pass
    lower = blob.lower()
    return {
        "openai": (
            "degraded"
            if re.search(r"openai|429|503|rate limit|upstream", lower)
            else "unknown"
        ),
        "elevenlabs": (
            "degraded"
            if re.search(r"elevenlabs|429|503|timeout", lower)
            else "unknown"
        ),
        "video_provider": (
            "degraded"
            if re.search(r"runway|veo|kling|provider.*timeout", lower)
            else "unknown"
        ),
    }


def queue_snapshot():
    out = {"redis": "unknown", "celery": "unknown", "signals": []}
    try:
        r = subprocess.run(
            ["bash", "-lc", "redis-cli ping || true"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        txt = (r.stdout + r.stderr).lower()
        out["redis"] = "ok" if "pong" in txt else "degraded"
        if txt.strip():
            out["signals"].append(txt[:200])
    except Exception:
        pass
    try:
        r = subprocess.run(
            ["bash", "-lc", "celery -A app inspect ping || true"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        txt = (r.stdout + r.stderr).lower()
        out["celery"] = "ok" if "pong" in txt else "degraded"
        if txt.strip():
            out["signals"].append(txt[:300])
    except Exception:
        pass
    try:
        r = subprocess.run(
            [
                "bash",
                "-lc",
                "docker ps --format '{{.Names}}' | grep -E 'worker|redis' || true",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.stdout.strip():
            out["signals"].append(r.stdout.strip()[:300])
    except Exception:
        pass
    return out


def ffmpeg_structured():
    out = []
    for base in [Path("logs"), Path("artifacts"), Path(".incident_report"), Path(".")]:
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if not f.is_file():
                continue
            if f.suffix.lower() not in {".log", ".txt", ".out"}:
                continue
            try:
                txt = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if "ffmpeg" not in txt.lower():
                continue
            tail = txt[-6000:]
            errs = re.findall(
                r"(ffmpeg.*|error.*|invalid data.*|moov atom not found.*|conversion failed.*)",
                tail,
                re.I,
            )
            if errs:
                out.append(
                    {
                        "file": str(f),
                        "stderr_lines": errs[:10],
                        "tail": tail[-1200:],
                    }
                )
    return out[:10]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--workflow-name", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    token = os.getenv("GITHUB_TOKEN", "")
    gh = (
        get_failed_steps(args.repo, args.run_id, token)
        if token
        else {"job_conclusion_map": {}, "failed_step_names": []}
    )

    evidence = {
        "workflow_name": args.workflow_name,
        "run_id": args.run_id,
        "failed_step_names": gh["failed_step_names"][:30],
        "job_conclusion_map": gh["job_conclusion_map"],
        "provider_health": provider_health(),
        "queue_snapshot": queue_snapshot(),
        "ffmpeg_stderr": ffmpeg_structured(),
    }

    Path(args.output).write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {"ok": True, "failed_steps": len(evidence["failed_step_names"])}, indent=2
        )
    )


if __name__ == "__main__":
    main()
