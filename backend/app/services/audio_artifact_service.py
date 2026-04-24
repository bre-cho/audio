import wave
from pathlib import Path

from app.core.config import AUDIO_ARTIFACT_DIR


def _write_silent_wav(path: Path, duration_seconds: float = 0.5) -> None:
    """Write a minimal silent WAV file so the artifact is playable."""
    sample_rate = 16000
    frames = int(sample_rate * duration_seconds)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * frames)


def write_audio_artifacts(job_id: str) -> dict:
    """Write placeholder audio files for a job and return their serving URLs.

    Files are written as silent WAV data but kept with .mp3 extensions so
    that the URL contract (/artifacts/audio/<id>.mp3) remains stable.
    Replace with real MP3 generation (e.g. via ffmpeg) when a TTS provider
    is integrated.
    """
    audio_dir = Path(AUDIO_ARTIFACT_DIR)
    audio_dir.mkdir(parents=True, exist_ok=True)

    preview_path = audio_dir / f"{job_id}.preview.mp3"
    output_path = audio_dir / f"{job_id}.mp3"

    _write_silent_wav(preview_path)
    _write_silent_wav(output_path)

    return {
        "preview_url": f"/artifacts/audio/{job_id}.preview.mp3",
        "output_url": f"/artifacts/audio/{job_id}.mp3",
    }
