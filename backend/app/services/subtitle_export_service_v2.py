from __future__ import annotations

import json
from pathlib import Path


def _srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _vtt_time(seconds: float) -> str:
    return _srt_time(seconds).replace(",", ".")


def export_transcript_bundle(transcript: dict, output_dir: str, basename: str = "transcript") -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / f"{basename}.json"
    srt_path = out / f"{basename}.srt"
    vtt_path = out / f"{basename}.vtt"
    json_path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
    segments = transcript.get("segments", [])
    srt_lines = []
    vtt_lines = ["WEBVTT", ""]
    for i, seg in enumerate(segments, 1):
        start, end, text = float(seg["start"]), float(seg["end"]), seg["text"]
        srt_lines.extend([str(i), f"{_srt_time(start)} --> {_srt_time(end)}", text, ""])
        vtt_lines.extend([f"{_vtt_time(start)} --> {_vtt_time(end)}", text, ""])
    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")
    vtt_path.write_text("\n".join(vtt_lines), encoding="utf-8")
    return {"json": str(json_path), "srt": str(srt_path), "vtt": str(vtt_path)}
