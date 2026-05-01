from __future__ import annotations

import math
import re
import struct
import subprocess
import wave
from pathlib import Path


def _run_ffprobe(path: str, entries: str, section: str = "format") -> dict[str, str]:
    """Run ffprobe and return key=value pairs from the requested section."""
    try:
        proc = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", f"{section}={entries}",
                "-of", "default=noprint_wrappers=1",
                path,
            ],
            capture_output=True, text=True, timeout=30,
        )
        result: dict[str, str] = {}
        for line in proc.stdout.splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                result[k.strip()] = v.strip()
        return result
    except Exception:
        return {}


def _measure_lufs(path: str) -> float | None:
    """Measure integrated LUFS via ffmpeg ebur128 filter."""
    try:
        proc = subprocess.run(
            [
                "ffmpeg", "-nostats", "-i", path,
                "-filter:a", "ebur128=framelog=verbose",
                "-f", "null", "-",
            ],
            capture_output=True, text=True, timeout=120,
        )
        # ffmpeg prints ebur128 summary to stderr
        match = re.search(r"I:\s*([-\d.]+)\s*LUFS", proc.stderr)
        if match:
            return float(match.group(1))
    except Exception:
        pass
    return None


def _measure_snr_wav(path: str) -> float | None:
    """Estimate SNR (dB) from WAV: noise floor from first 300 ms vs signal RMS."""
    try:
        with wave.open(path, "rb") as wf:
            sampwidth = wf.getsampwidth()
            rate = wf.getframerate()
            channels = wf.getnchannels()
            frames = wf.readframes(wf.getnframes())
        if sampwidth != 2:
            return None
        count = len(frames) // 2
        samples = struct.unpack(f"<{count}h", frames[: count * 2])
        # Mono-fold (average channels)
        if channels > 1:
            mono = [
                sum(samples[i + ch] for ch in range(channels)) // channels
                for i in range(0, len(samples), channels)
            ]
        else:
            mono = list(samples)
        if not mono:
            return None
        noise_len = max(1, int(rate * 0.3))  # first 300 ms
        noise = mono[:noise_len]
        noise_rms = math.sqrt(sum(s * s for s in noise) / len(noise)) if noise else 1.0
        signal_rms = math.sqrt(sum(s * s for s in mono) / len(mono))
        if noise_rms < 1:
            noise_rms = 1.0
        return round(20 * math.log10(signal_rms / noise_rms), 2) if signal_rms > 0 else None
    except Exception:
        return None


def build_quality_report(
    *,
    path: str | None = None,
    duration_ms: int | None = None,
    rms: int | None = None,
    peak: int | None = None,
    sample_rate: int | None = None,
    channels: int | None = None,
) -> dict:
    """Build a comprehensive audio quality report.

    When ``path`` is provided the report is enriched with LUFS, SNR, and
    codec metadata via ffprobe/ffmpeg.  Legacy callers that only provide
    numeric fields still work; they receive a ``status: basic`` report.
    """
    report: dict = {
        "duration_ms": duration_ms,
        "rms": rms,
        "peak": peak,
        "sample_rate": sample_rate,
        "channels": channels,
        "status": "basic",
    }

    if not path:
        return report

    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        report["status"] = "error"
        report["error"] = "file_missing_or_empty"
        return report

    # Probe codec / format metadata
    fmt_data = _run_ffprobe(
        path,
        "duration,size,bit_rate",
        section="format",
    )
    stream_data = _run_ffprobe(
        path,
        "codec_name,sample_rate,channels,bits_per_sample,bit_rate",
        section="stream",
    )

    probe_duration_sec = float(fmt_data.get("duration", 0) or 0)
    probe_sample_rate = int(stream_data.get("sample_rate", 0) or 0)
    probe_channels = int(stream_data.get("channels", 0) or 0)
    probe_codec = stream_data.get("codec_name", "unknown")
    probe_bit_rate = int(fmt_data.get("bit_rate", 0) or 0)
    probe_size_bytes = int(fmt_data.get("size", 0) or 0)

    report.update(
        {
            "duration_sec": probe_duration_sec,
            "duration_ms": round(probe_duration_sec * 1000) if probe_duration_sec else duration_ms,
            "sample_rate": probe_sample_rate or sample_rate,
            "channels": probe_channels or channels,
            "codec": probe_codec,
            "bit_rate_bps": probe_bit_rate,
            "file_size_bytes": probe_size_bytes,
        }
    )

    # LUFS measurement (requires a full decode pass; ~real-time for short clips)
    lufs = _measure_lufs(path)
    report["lufs_integrated"] = lufs

    # SNR from WAV (only for uncompressed)
    if p.suffix.lower() == ".wav":
        report["snr_db"] = _measure_snr_wav(path)
    else:
        report["snr_db"] = None

    # Quality assessment
    issues: list[str] = []
    if lufs is not None and lufs < -23:
        issues.append("too_quiet")
    if lufs is not None and lufs > -6:
        issues.append("too_loud_clipping_risk")
    if probe_duration_sec < 0.2:
        issues.append("duration_too_short")

    report["issues"] = issues
    report["status"] = "ok" if not issues else "warning"
    return report
