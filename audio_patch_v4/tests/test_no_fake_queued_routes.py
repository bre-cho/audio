from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "backend" / "app" / "api"


def test_no_fake_queued_without_job_creation():
    offenders = []
    for path in API_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if '"status": "queued"' in text or "'status': 'queued'" in text:
            has_job = re.search(r"create_.*job|enqueue|delay\(|apply_async\(|persist_.*job", text)
            if not has_job:
                offenders.append(str(path))
    assert not offenders, "Fake queued route(s) found without real job creation: " + ", ".join(offenders)
