from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_no_duplicate_elevenlabs_adapters_after_v4_cleanup():
    candidates = list((ROOT / "backend" / "app").rglob("*elevenlabs*.py"))
    active = [p for p in candidates if "deprecated" not in p.read_text(encoding="utf-8", errors="ignore").lower()]
    assert len(active) <= 1, "Keep one active ElevenLabs adapter; mark others deprecated/wrappers: " + ", ".join(map(str, active))
