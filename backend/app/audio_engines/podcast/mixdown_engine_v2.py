from __future__ import annotations

import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PodcastClip:
    path: str
    start_sec: float = 0.0
    gain: float = 1.0


def _resample_to_wav(src_path: str, target_rate: int = 44100) -> str:
    """Re-encode any audio file to mono 16-bit PCM WAV at ``target_rate`` Hz.

    Returns the path to the resampled WAV (written alongside the source with
    a ``.resampled.wav`` suffix so the original is untouched).
    """
    dst = Path(src_path).with_suffix(".resampled.wav")
    cmd = [
        "ffmpeg", "-y", "-i", src_path,
        "-ac", "1", "-ar", str(target_rate), "-sample_fmt", "s16",
        str(dst),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0 or not dst.exists() or dst.stat().st_size == 0:
        raise RuntimeError(f"podcast_mixer_resample_failed:{proc.stderr[-400:]}")
    return str(dst)


class PodcastMixdownEngineV2:
    """Lightweight PCM WAV mixdown with automatic resampling.

    Clips at any sample rate or format are resampled to ``target_sample_rate``
    (default 44 100 Hz) via ffmpeg before mixing so the engine always produces
    a consistently-formatted output.
    """

    def mix_wav_clips(
        self,
        clips: list[PodcastClip],
        output_path: str,
        sample_rate: int = 44100,
    ) -> str:
        if not clips:
            raise ValueError("clips_required")

        buffers: list[tuple[int, list[int]]] = []
        total_len = 0
        resampled_paths: list[str] = []

        for clip in clips:
            src = clip.path
            try:
                with wave.open(src, "rb") as wf:
                    width = wf.getsampwidth()
                    rate = wf.getframerate()
                needs_resample = (width != 2 or rate != sample_rate)
            except Exception:
                # Non-WAV or unreadable — always resample
                needs_resample = True
                rate = 0

            if needs_resample:
                src = _resample_to_wav(src, sample_rate)
                resampled_paths.append(src)

            with wave.open(src, "rb") as wf:
                if wf.getsampwidth() != 2:
                    raise ValueError(f"only_16bit_pcm_wav_supported_after_resample:{src}")
                frames = wf.readframes(wf.getnframes())

            samples = [
                int.from_bytes(frames[i : i + 2], "little", signed=True)
                for i in range(0, len(frames), 2)
            ]
            start = int(clip.start_sec * sample_rate)
            buffers.append(
                (start, [max(-32768, min(32767, int(s * clip.gain))) for s in samples])
            )
            total_len = max(total_len, start + len(samples))

        mixed = [0] * total_len
        for start, samples in buffers:
            for i, s in enumerate(samples):
                mixed[start + i] = max(-32768, min(32767, mixed[start + i] + s))

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(out), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(
                b"".join(int(s).to_bytes(2, "little", signed=True) for s in mixed)
            )

        # Clean up temporary resampled files
        for tmp in resampled_paths:
            try:
                Path(tmp).unlink(missing_ok=True)
            except OSError:
                pass

        return str(out)
