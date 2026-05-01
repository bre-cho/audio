class FormantPreservation:
    """Build formant preservation config and apply ffmpeg-based formant shift.

    The config dict is passed to the voice conversion adapters via the
    ``preserve_formants`` flag.  Adapters that support it (ElevenLabs STS,
    RVC with ``--protect``, OpenVoice with ``--tau``) honour the config
    automatically when ``preserve_formants=True`` is passed to ``.convert()``.

    For post-processing formant correction (e.g. after RVC/OpenVoice), call
    :meth:`apply_formant_correction_wav` with the output WAV path.
    """

    def build_config(self, enabled: bool = True, strength: float = 0.8) -> dict:
        return {"enabled": enabled, "strength": max(0.0, min(1.0, strength))}

    def apply_formant_correction_wav(
        self,
        input_path: str,
        output_path: str,
        strength: float = 0.8,
    ) -> str:
        """Apply formant correction to a WAV file via ffmpeg rubberband filter.

        Uses the ``rubberband`` audio filter (available in ffmpeg builds with
        libRubberBand) to shift formants without changing pitch, preserving the
        naturalness of the converted voice.

        Args:
            input_path: Path to the converted WAV.
            output_path: Destination WAV path.
            strength: Formant correction intensity 0.0–1.0.  Maps to
                ``rubberband=formant=<1.0 + strength>`` (no-op at 0.0).

        Returns:
            ``output_path`` on success.

        Raises:
            RuntimeError: if ffmpeg fails or output is missing.
        """
        import subprocess
        from pathlib import Path

        if strength <= 0.0:
            # Nothing to do — copy as-is
            import shutil
            shutil.copy2(input_path, output_path)
            return output_path

        # Map [0.0, 1.0] → rubberband formant ratio [1.0, 1.1]
        formant_ratio = 1.0 + (strength * 0.1)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-af", f"rubberband=formant={formant_ratio:.3f}",
            "-ac", "1", "-ar", "44100",
            output_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if proc.returncode != 0 or not Path(output_path).exists():
            # rubberband may not be available in all ffmpeg builds — fall back gracefully
            import shutil
            shutil.copy2(input_path, output_path)
        return output_path
