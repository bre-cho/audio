from __future__ import annotations

from app.audio_engines.podcast.mixdown_engine_v2 import PodcastClip, PodcastMixdownEngineV2
from app.services.audio_signal_validator import validate_audio_signal


def mix_podcast_from_wav_clips(clips: list[dict], output_path: str) -> dict:
    typed = [PodcastClip(path=c["path"], start_sec=float(c.get("start_sec", 0)), gain=float(c.get("gain", 1))) for c in clips]
    path = PodcastMixdownEngineV2().mix_wav_clips(typed, output_path)
    report = validate_audio_signal(path)
    if not report.ok:
        raise RuntimeError(f"podcast_mixdown_failed_signal_gate:{report.reason}")
    return {"path": path, "signal": report.__dict__}
