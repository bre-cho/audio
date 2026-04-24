from pathlib import Path

from app.core.config import AUDIO_ARTIFACT_DIR

# Minimal valid ID3v2 header — 10 bytes — recognised as audio/mpeg by most players
_MIN_MP3_PLACEHOLDER = b"\x49\x44\x33\x03\x00\x00\x00\x00\x00\x00"


def write_audio_artifacts(job_id: str) -> dict:
    """Write placeholder MP3 files for a job and return their serving URLs."""
    audio_dir = Path(AUDIO_ARTIFACT_DIR)
    audio_dir.mkdir(parents=True, exist_ok=True)

    preview_path = audio_dir / f"{job_id}.preview.mp3"
    output_path = audio_dir / f"{job_id}.mp3"

    preview_path.write_bytes(_MIN_MP3_PLACEHOLDER)
    output_path.write_bytes(_MIN_MP3_PLACEHOLDER)

    return {
        "preview_url": f"/artifacts/audio/{job_id}.preview.mp3",
        "output_url": f"/artifacts/audio/{job_id}.mp3",
    }
