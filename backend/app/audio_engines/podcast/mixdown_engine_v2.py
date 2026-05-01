from __future__ import annotations

import wave
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PodcastClip:
    path: str
    start_sec: float = 0.0
    gain: float = 1.0


class PodcastMixdownEngineV2:
    """Lightweight PCM WAV mixdown. For MP3/provider outputs, decode with ffmpeg before calling."""

    def mix_wav_clips(self, clips: list[PodcastClip], output_path: str, sample_rate: int = 44100) -> str:
        if not clips:
            raise ValueError("clips_required")
        buffers: list[tuple[int, list[int]]] = []
        total_len = 0
        for clip in clips:
            with wave.open(clip.path, "rb") as wf:
                if wf.getsampwidth() != 2:
                    raise ValueError("only_16bit_pcm_wav_supported")
                rate = wf.getframerate()
                if rate != sample_rate:
                    raise ValueError(f"sample_rate_mismatch:{rate}!={sample_rate}")
                frames = wf.readframes(wf.getnframes())
            samples = [int.from_bytes(frames[i:i+2], "little", signed=True) for i in range(0, len(frames), 2)]
            start = int(clip.start_sec * sample_rate)
            buffers.append((start, [max(-32768, min(32767, int(s * clip.gain))) for s in samples]))
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
            wf.writeframes(b"".join(int(s).to_bytes(2, "little", signed=True) for s in mixed))
        return str(out)
