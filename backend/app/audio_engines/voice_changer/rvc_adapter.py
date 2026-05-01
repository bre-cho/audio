from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

# Allow only alphanumeric, underscore, and hyphen in voice IDs to prevent
# path traversal / command injection when building model file paths.
_VOICE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")


@dataclass(frozen=True)
class VoiceConversionResult:
    output_path: str
    provider: str
    target_voice_id: str
    metadata: dict


def _validate_voice_id(voice_id: str) -> None:
    if not _VOICE_ID_RE.match(voice_id):
        raise ValueError(
            f"rvc_invalid_voice_id: voice_id must match [a-zA-Z0-9_-]{{1,128}}, got '{voice_id}'"
        )


class RVCVoiceConversionAdapter:
    """Voice conversion via Retrieval-based Voice Conversion (RVC).

    Required environment variables:
    - ``RVC_MODEL_DIR`` — directory containing per-voice-id ``.pth`` checkpoints
      and optional ``.index`` files (e.g. ``/models/rvc/``).
    - ``RVC_SCRIPT_PATH`` — path to the ``infer_batch_rvc.py`` CLI entry point
      (from the RVC repository clone, e.g. ``/opt/rvc/infer_batch_rvc.py``).

    Optional environment variables:
    - ``RVC_F0_METHOD`` — pitch extraction method: ``harvest`` (default),
      ``pm``, ``crepe``, or ``rmvpe``.
    - ``RVC_HOP_LENGTH`` — hop length for crepe/rmvpe (default 128).
    - ``RVC_TRANSPOSE`` — semitone transposition (default 0).

    The adapter shells out to the RVC Python CLI so no model loading happens
    inside the FastAPI process, keeping memory usage bounded.
    """

    provider_name = "rvc"

    def convert(
        self,
        *,
        input_path: str,
        target_voice_id: str,
        output_path: str,
        preserve_formants: bool = True,
    ) -> VoiceConversionResult:
        _validate_voice_id(target_voice_id)

        model_dir = os.getenv("RVC_MODEL_DIR", "").strip()
        rvc_script = os.getenv("RVC_SCRIPT_PATH", "").strip()
        if not model_dir or not rvc_script:
            raise RuntimeError(
                "rvc_not_configured: set RVC_MODEL_DIR and RVC_SCRIPT_PATH to enable "
                "VOICE_CONVERSION_PROVIDER=rvc"
            )
        if not Path(rvc_script).exists():
            raise RuntimeError(
                f"rvc_script_not_found: RVC_SCRIPT_PATH={rvc_script!r} does not exist"
            )

        model_path = self._resolve_model(model_dir, target_voice_id)
        index_path = self._find_index(model_dir, target_voice_id)

        f0_method = os.getenv("RVC_F0_METHOD", "harvest")
        hop_length = os.getenv("RVC_HOP_LENGTH", "128")
        transpose = os.getenv("RVC_TRANSPOSE", "0")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "python", rvc_script,
            "--input_path", input_path,
            "--output_path", output_path,
            "--model_name", model_path,
            "--f0_method", f0_method,
            "--transpose", transpose,
            "--hop_length", hop_length,
        ]
        if index_path:
            cmd += ["--index_path", index_path, "--index_rate", "0.75"]
        if preserve_formants:
            cmd += ["--protect", "0.33"]

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if proc.returncode != 0:
            raise RuntimeError(
                f"rvc_conversion_failed:{proc.stderr[-600:]}"
            )

        out = Path(output_path)
        if not out.exists() or out.stat().st_size == 0:
            raise RuntimeError("rvc_output_missing_or_empty")

        return VoiceConversionResult(
            output_path=output_path,
            provider=self.provider_name,
            target_voice_id=target_voice_id,
            metadata={
                "model_path": model_path,
                "f0_method": f0_method,
                "transpose": transpose,
                "index_path": index_path or "",
                "preserve_formants": preserve_formants,
            },
        )

    @staticmethod
    def _resolve_model(model_dir: str, voice_id: str) -> str:
        """Locate the .pth checkpoint for the given voice_id.

        ``voice_id`` has already been validated by ``_validate_voice_id``.
        """
        base = Path(model_dir).resolve()
        # Accept: <model_dir>/<voice_id>.pth  OR  <model_dir>/<voice_id>/<voice_id>.pth
        candidates = [
            base / f"{voice_id}.pth",
            base / voice_id / f"{voice_id}.pth",
        ]
        for candidate in candidates:
            resolved = candidate.resolve()
            # Ensure the resolved path stays within model_dir (defence-in-depth)
            if resolved.is_relative_to(base) and resolved.exists():
                return str(resolved)
        raise RuntimeError(
            f"rvc_model_not_found: no .pth checkpoint for voice_id '{voice_id}' "
            f"under RVC_MODEL_DIR={model_dir}"
        )

    @staticmethod
    def _find_index(model_dir: str, voice_id: str) -> str | None:
        """Return the .index file if it exists alongside the model checkpoint."""
        base = Path(model_dir).resolve()
        candidates = [
            base / f"{voice_id}.index",
            base / voice_id / f"{voice_id}.index",
        ]
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved.is_relative_to(base) and resolved.exists():
                return str(resolved)
        return None
