from __future__ import annotations

import subprocess
from pathlib import Path


class PodcastDuckingService:
    """Apply BGM ducking to a voice track using ffmpeg amix.

    The BGM is mixed at a reduced volume (default -14 dB / ~0.2 linear) under
    the voice track so speech stays intelligible.
    """

    DEFAULT_BGM_VOLUME: float = 0.15  # linear gain for BGM under voice

    def apply_ducking(
        self,
        voice_track_path: str,
        bgm_path: str,
        output_path: str,
        bgm_volume: float | None = None,
    ) -> str:
        """Mix ``bgm_path`` under ``voice_track_path`` with reduced gain.

        Returns the path to the mixed output WAV.
        """
        bgm_vol = bgm_volume if bgm_volume is not None else self.DEFAULT_BGM_VOLUME
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # ffmpeg filter graph:
        #   [0:a] — voice track at full volume
        #   [1:a] — BGM scaled to bgm_vol
        #   amix both inputs, normalise to prevent clipping
        filter_graph = (
            f"[0:a]volume=1.0[voice];"
            f"[1:a]volume={bgm_vol:.4f}[bgm];"
            f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=3[out]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", voice_track_path,
            "-i", bgm_path,
            "-filter_complex", filter_graph,
            "-map", "[out]",
            "-ac", "1", "-ar", "44100",
            output_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"podcast_ducking_ffmpeg_failed:{proc.stderr[-500:]}")
        return output_path
