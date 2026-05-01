from __future__ import annotations

def _fmt_srt_time(seconds: float) -> str:
    ms = int((seconds - int(seconds)) * 1000)
    total = int(seconds)
    s = total % 60
    m = (total // 60) % 60
    h = total // 3600
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def _fmt_vtt_time(seconds: float) -> str:
    return _fmt_srt_time(seconds).replace(",", ".")

def transcript_to_srt(segments: list[dict]) -> str:
    lines = []
    for i, seg in enumerate(segments, 1):
        start = float(seg.get("start", seg.get("start_time", 0)))
        end = float(seg.get("end", seg.get("end_time", start + 1)))
        text = seg.get("text") or seg.get("word") or ""
        lines += [str(i), f"{_fmt_srt_time(start)} --> {_fmt_srt_time(end)}", text, ""]
    return "\n".join(lines)

def transcript_to_vtt(segments: list[dict]) -> str:
    body = transcript_to_srt(segments).replace(",", ".")
    return "WEBVTT\n\n" + "\n".join(line for line in body.splitlines() if not line.isdigit())
