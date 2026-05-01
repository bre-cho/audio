from __future__ import annotations

import subprocess
from pathlib import Path
from uuid import uuid4


class AudioDecodeError(RuntimeError):
    pass


def decode_to_wav(input_path: str, output_dir: str = "artifacts/audio_decoded") -> str:
    src = Path(input_path)
    if not src.exists() or src.stat().st_size == 0:
        raise AudioDecodeError("input_audio_missing_or_empty")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / f"{uuid4()}.wav"
    cmd = ["ffmpeg", "-y", "-i", str(src), "-ac", "1", "-ar", "44100", str(dst)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not dst.exists() or dst.stat().st_size == 0:
        raise AudioDecodeError(f"ffmpeg_decode_failed:{proc.stderr[-500:]}")
    return str(dst)
