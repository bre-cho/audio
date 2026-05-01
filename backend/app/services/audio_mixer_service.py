from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


class AudioMixerService:
    """Mix voice tracks with optional BGM using ffmpeg with LUFS normalisation.

    Target loudness: -14 LUFS (streaming standard).
    BGM is mixed at a reduced volume (-18 dB) so speech stays intelligible.
    """

    TARGET_LUFS: float = -14.0
    BGM_GAIN_DB: float = -18.0

    def mix(
        self,
        voice_tracks: list[str],
        bgm_path: str | None,
        output_path: str,
        ducking: bool = True,
        target_lufs: float | None = None,
    ) -> dict:
        """Mix one or more voice tracks with optional BGM into a LUFS-normalised output.

        Args:
            voice_tracks: Ordered list of audio file paths (MP3, WAV, FLAC …).
            bgm_path: Optional background music file path.  Mixed at BGM_GAIN_DB
                      relative to the voice tracks.
            output_path: Destination path (WAV).
            ducking: When True, applies side-chain ducking so BGM dips when
                     speech is present (requires ffmpeg's ``sidechaincompress``).
            target_lufs: Override normalisation target (default -14 LUFS).

        Returns:
            Dict with output_path, duration_sec, lufs_measured, and ffmpeg_stderr
            (truncated) for diagnostics.
        """
        if not voice_tracks:
            raise ValueError("voice_tracks must not be empty")

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        target = target_lufs if target_lufs is not None else self.TARGET_LUFS

        # Step 1: Concatenate / mix all voice tracks into a single WAV.
        concat_wav = self._concat_voice_tracks(voice_tracks, out)

        # Step 2: Optionally mix BGM underneath.
        if bgm_path and Path(bgm_path).exists():
            mixed_wav = out.with_suffix(".premix.wav")
            self._mix_bgm(str(concat_wav), bgm_path, str(mixed_wav), ducking=ducking)
            source = mixed_wav
        else:
            source = concat_wav

        # Step 3: LUFS normalisation.
        lufs_measured = self._apply_loudnorm(str(source), output_path, target_lufs=target)

        # Clean up intermediate files.
        for tmp in [concat_wav, out.with_suffix(".premix.wav")]:
            try:
                if tmp.exists() and tmp != out:
                    tmp.unlink()
            except OSError:
                pass

        # Measure output duration.
        duration = self._probe_duration(output_path)
        return {
            "output_path": output_path,
            "duration_sec": duration,
            "lufs_measured": lufs_measured,
            "target_lufs": target,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _concat_voice_tracks(self, tracks: list[str], base_path: Path) -> Path:
        """Concatenate multiple tracks sequentially into a single 44100 Hz mono WAV."""
        dest = base_path.with_suffix(".concat.wav")
        if len(tracks) == 1:
            # Single track: just convert/normalise sample rate
            cmd = [
                "ffmpeg", "-y", "-i", tracks[0],
                "-ac", "1", "-ar", "44100", str(dest),
            ]
            self._run(cmd)
            return dest

        # Build a concat filter for N inputs
        inputs: list[str] = []
        for t in tracks:
            inputs += ["-i", t]
        filter_str = "".join(f"[{i}:a]" for i in range(len(tracks)))
        filter_str += f"concat=n={len(tracks)}:v=0:a=1[out]"
        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_str,
            "-map", "[out]",
            "-ac", "1", "-ar", "44100",
            str(dest),
        ]
        self._run(cmd)
        return dest

    def _mix_bgm(self, voice_path: str, bgm_path: str, output_path: str, ducking: bool) -> None:
        """Mix BGM under voice track with optional side-chain ducking."""
        if ducking:
            # Side-chain compressor: BGM dips 15 dB when voice is active
            filter_graph = (
                f"[0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=mono[voice];"
                f"[1:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=mono,"
                f"volume={self.BGM_GAIN_DB}dB[bgm];"
                f"[bgm][voice]sidechaincompress=threshold=0.01:ratio=20:attack=200:release=1000[bgm_ducked];"
                f"[voice][bgm_ducked]amix=inputs=2:duration=first:dropout_transition=3[out]"
            )
        else:
            filter_graph = (
                f"[0:a]volume=1.0[voice];"
                f"[1:a]volume={self.BGM_GAIN_DB}dB[bgm];"
                f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=3[out]"
            )
        cmd = [
            "ffmpeg", "-y",
            "-i", voice_path,
            "-i", bgm_path,
            "-filter_complex", filter_graph,
            "-map", "[out]",
            "-ac", "1", "-ar", "44100",
            output_path,
        ]
        self._run(cmd)

    def _apply_loudnorm(self, src: str, dst: str, target_lufs: float) -> float | None:
        """Apply ffmpeg loudnorm filter; return measured LUFS or None on error."""
        cmd = [
            "ffmpeg", "-y", "-i", src,
            "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
            "-ac", "1", "-ar", "44100",
            dst,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if proc.returncode != 0 or not Path(dst).exists():
            raise RuntimeError(f"audio_mixer_loudnorm_failed:{proc.stderr[-500:]}")
        # Parse measured LUFS from ffmpeg stderr (loudnorm outputs JSON-like block)
        return self._parse_lufs(proc.stderr)

    def _probe_duration(self, path: str) -> float:
        """Return audio duration in seconds via ffprobe."""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    path,
                ],
                capture_output=True, text=True, timeout=30,
            )
            return float(result.stdout.strip()) if result.stdout.strip() else 0.0
        except Exception:
            return 0.0

    @staticmethod
    def _parse_lufs(stderr: str) -> float | None:
        """Extract measured_I (integrated LUFS) from ffmpeg loudnorm stderr output."""
        import re
        match = re.search(r'"input_i"\s*:\s*"([^"]+)"', stderr)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None

    @staticmethod
    def _run(cmd: list[str]) -> None:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode != 0:
            raise RuntimeError(f"audio_mixer_ffmpeg_error:{proc.stderr[-500:]}")
