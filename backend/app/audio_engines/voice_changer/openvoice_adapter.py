from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VoiceConversionResult:
    output_path: str
    provider: str
    target_voice_id: str
    metadata: dict


class OpenVoiceConversionAdapter:
    """Voice tone-color transfer via OpenVoice (MyShell-AI/OpenVoice).

    Required environment variables:
    - ``OPENVOICE_MODEL_PATH`` — path to the OpenVoice checkpoint directory
      (e.g. ``/opt/openvoice/checkpoints_v2``).
    - ``OPENVOICE_SCRIPT_PATH`` — path to the OpenVoice inference entry point
      (e.g. ``/opt/openvoice/run_conversion.py``).
    - ``OPENVOICE_REFERENCE_DIR`` — directory containing per-voice-id reference
      audio files used to extract tone-color embeddings (e.g. ``/models/openvoice/refs``).
      Expected file: ``<reference_dir>/<voice_id>.wav`` (or .mp3).

    Optional environment variables:
    - ``OPENVOICE_DEVICE`` — ``cuda`` (default if GPU available) or ``cpu``.
    - ``OPENVOICE_TAU`` — style adaptation strength 0–1 (default 0.3).
    """

    provider_name = "openvoice"

    def convert(
        self,
        *,
        input_path: str,
        target_voice_id: str,
        output_path: str,
        preserve_formants: bool = True,
    ) -> VoiceConversionResult:
        model_path = os.getenv("OPENVOICE_MODEL_PATH", "").strip()
        script_path = os.getenv("OPENVOICE_SCRIPT_PATH", "").strip()
        ref_dir = os.getenv("OPENVOICE_REFERENCE_DIR", "").strip()

        if not model_path or not script_path or not ref_dir:
            raise RuntimeError(
                "openvoice_not_configured: set OPENVOICE_MODEL_PATH, "
                "OPENVOICE_SCRIPT_PATH, and OPENVOICE_REFERENCE_DIR to enable "
                "VOICE_CONVERSION_PROVIDER=openvoice"
            )

        reference_audio = self._resolve_reference(ref_dir, target_voice_id)
        device = os.getenv("OPENVOICE_DEVICE", "cuda")
        tau = os.getenv("OPENVOICE_TAU", "0.3")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "python", script_path,
            "--source", input_path,
            "--reference", reference_audio,
            "--output", output_path,
            "--checkpoint_dir", model_path,
            "--device", device,
            "--tau", tau,
        ]

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode != 0:
            raise RuntimeError(
                f"openvoice_conversion_failed:{proc.stderr[-600:]}"
            )

        out = Path(output_path)
        if not out.exists() or out.stat().st_size == 0:
            raise RuntimeError("openvoice_output_missing_or_empty")

        return VoiceConversionResult(
            output_path=output_path,
            provider=self.provider_name,
            target_voice_id=target_voice_id,
            metadata={
                "model_path": model_path,
                "reference_audio": reference_audio,
                "device": device,
                "tau": tau,
            },
        )

    @staticmethod
    def _resolve_reference(ref_dir: str, voice_id: str) -> str:
        """Find the reference audio file for the given voice_id."""
        base = Path(ref_dir)
        for ext in (".wav", ".mp3", ".flac", ".ogg"):
            candidate = base / f"{voice_id}{ext}"
            if candidate.exists():
                return str(candidate)
        raise RuntimeError(
            f"openvoice_reference_not_found: no reference audio for voice_id '{voice_id}' "
            f"under OPENVOICE_REFERENCE_DIR={ref_dir}. "
            f"Add a WAV/MP3/FLAC file named '{voice_id}.wav' (or .mp3/.flac/.ogg)."
        )
