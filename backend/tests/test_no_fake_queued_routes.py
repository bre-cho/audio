from pathlib import Path

API_FILES = [
    "backend/app/api/bgm.py",
    "backend/app/api/sound_effects.py",
    "backend/app/api/transcription.py",
    "backend/app/api/localization.py",
    "backend/app/api/voice_changer.py",
]


def test_no_fake_queued_literal_in_unwired_routes():
    repo = Path(__file__).resolve().parents[1].parent
    offenders = []
    for rel in API_FILES:
        path = repo / rel
        if path.exists() and '"status": "queued"' in path.read_text(encoding="utf-8"):
            offenders.append(rel)
    assert not offenders, f"Fake queued responses remain: {offenders}"
