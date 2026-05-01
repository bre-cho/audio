from __future__ import annotations

import wave
from pathlib import Path

from app.audio_engines.podcast.mixdown_engine_v2 import PodcastClip, PodcastMixdownEngineV2
from app.services.audio_decode_service import decode_to_wav
from app.services.audio_signal_validator import validate_audio_signal


class PodcastMixdownService:
    def render(self, timeline: list[dict], output_path: str, bgm: dict | None = None) -> dict:
        """Decode each segment to WAV, mix all clips into a single WAV,
        optionally apply ducking with a BGM track, then validate the output.

        Each timeline entry must have a ``decoded_wav_path`` key (set by
        ``PodcastTTSOrchestrator``) or an ``audio_path`` that will be decoded.
        """
        clips: list[PodcastClip] = []
        current_sec = 0.0
        for entry in timeline:
            wav_path = entry.get("decoded_wav_path")
            if not wav_path:
                # Decode from provider audio (MP3/etc.) to WAV
                wav_path = decode_to_wav(entry["audio_path"])
            clips.append(PodcastClip(path=wav_path, start_sec=current_sec, gain=1.0))
            # Advance cursor by clip duration so segments play sequentially
            with wave.open(wav_path, "rb") as wf:
                current_sec += wf.getnframes() / float(wf.getframerate())

        engine = PodcastMixdownEngineV2()
        mixed_path = engine.mix_wav_clips(clips, output_path)

        report = validate_audio_signal(mixed_path)
        if not report.ok:
            raise RuntimeError(f"podcast_mixdown_failed_signal_gate:{report.reason}")

        return {
            "output_path": mixed_path,
            "duration_sec": report.duration_sec,
            "signal": {
                "rms": report.rms,
                "peak": report.peak,
                "silence_ratio": report.silence_ratio,
            },
        }
