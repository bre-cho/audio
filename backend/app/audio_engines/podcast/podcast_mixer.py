from __future__ import annotations

import io
import math
import struct
import wave
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Podcast Mixer — pure Python
# Accepts a list of segments, each containing WAV bytes.
# Normalises all segments to a common format, inserts silence between
# segments, then concatenates with configurable crossfade.
# ---------------------------------------------------------------------------

_DEFAULT_SAMPLE_RATE = 44100
_DEFAULT_CHANNELS = 1
_DEFAULT_SAMPWIDTH = 2  # 16-bit
_DEFAULT_PAUSE_MS = 500  # silence between segments
_CROSSFADE_MS = 30  # crossfade overlap at segment junctions


@dataclass
class MixerSegment:
    audio_wav: bytes
    speaker: str = ""
    pause_after_ms: int = _DEFAULT_PAUSE_MS
    metadata: dict = field(default_factory=dict)


# --- WAV I/O ----------------------------------------------------------------

def _read_wav(data: bytes) -> tuple[list[int], int, int, int]:
    with wave.open(io.BytesIO(data), "rb") as wf:
        nch = wf.getnchannels()
        sw = wf.getsampwidth()
        fr = wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    if sw == 1:
        return [b - 128 for b in raw], nch, sw, fr
    elif sw == 2:
        count = len(raw) // 2
        return list(struct.unpack(f"<{count}h", raw[: count * 2])), nch, sw, fr
    else:
        raise ValueError(f"unsupported sample width: {sw}")


def _write_wav(samples: list[int], nchannels: int, sampwidth: int, framerate: int) -> bytes:
    if sampwidth == 1:
        raw = bytes(max(0, min(255, s + 128)) for s in samples)
    else:
        raw = struct.pack(f"<{len(samples)}h", *(max(-32768, min(32767, s)) for s in samples))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(nchannels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(raw)
    return buf.getvalue()


# --- Resampling / format conversion -----------------------------------------

def _resample_nearest(samples: list[int], src_rate: int, dst_rate: int) -> list[int]:
    """Nearest-neighbour resampling — good enough for mono voice audio."""
    if src_rate == dst_rate or not samples:
        return samples
    ratio = src_rate / dst_rate
    new_len = max(1, int(len(samples) / ratio))
    return [samples[min(int(i * ratio), len(samples) - 1)] for i in range(new_len)]


def _to_mono(samples: list[int], nchannels: int) -> list[int]:
    if nchannels == 1:
        return samples
    return [
        int(sum(samples[i : i + nchannels]) / nchannels)
        for i in range(0, len(samples) - nchannels + 1, nchannels)
    ]


def _convert_sampwidth(samples: list[int], src_width: int, dst_width: int) -> list[int]:
    if src_width == dst_width:
        return samples
    if src_width == 1 and dst_width == 2:
        return [s * 257 for s in samples]  # 128-scale → 32767-scale approx
    if src_width == 2 and dst_width == 1:
        return [s // 257 for s in samples]
    return samples


def _normalise_segment(
    samples: list[int],
    nchannels: int,
    sampwidth: int,
    framerate: int,
    *,
    target_rate: int,
    target_channels: int,
    target_width: int,
    target_peak_ratio: float = 0.85,
) -> list[int]:
    samples = _to_mono(samples, nchannels)
    samples = _resample_nearest(samples, framerate, target_rate)
    samples = _convert_sampwidth(samples, sampwidth, target_width)
    # Per-segment normalise
    max_val = 32767 if target_width == 2 else 127
    peak = max((abs(s) for s in samples), default=0)
    if peak > 0:
        gain = (max_val * target_peak_ratio) / peak
        samples = [int(s * gain) for s in samples]
    if target_channels == 2:
        samples = [v for s in samples for v in (s, s)]  # mono→stereo dup
    return samples


# --- Crossfade / silence ----------------------------------------------------

def _silence(n_samples: int) -> list[int]:
    return [0] * n_samples


def _crossfade(a: list[int], b: list[int], n: int) -> list[int]:
    """Crossfade last n samples of a with first n samples of b."""
    if n <= 0 or len(a) < n or len(b) < n:
        return a + b
    faded = list(a[:-n])
    for i in range(n):
        t = i / n
        faded.append(int(a[-n + i] * (1 - t) + b[i] * t))
    faded.extend(b[n:])
    return faded


# --- Main mixer function ----------------------------------------------------

def mix_podcast_wav(
    *,
    segments: list[MixerSegment],
    target_rate: int = _DEFAULT_SAMPLE_RATE,
    target_channels: int = _DEFAULT_CHANNELS,
    crossfade_ms: int = _CROSSFADE_MS,
) -> tuple[bytes, dict]:
    """Mix podcast segments into a single WAV.

    Returns (output_wav_bytes, report_dict).
    """
    if not segments:
        raise ValueError("no segments provided")

    target_width = _DEFAULT_SAMPWIDTH
    crossfade_samples = int(target_rate * crossfade_ms / 1000) * target_channels
    mixed: list[int] = []
    segment_reports: list[dict] = []

    for idx, seg in enumerate(segments):
        raw_samples, nch, sw, fr = _read_wav(seg.audio_wav)
        norm = _normalise_segment(
            raw_samples, nch, sw, fr,
            target_rate=target_rate,
            target_channels=target_channels,
            target_width=target_width,
        )
        duration_ms = int(len(norm) / (target_rate * target_channels) * 1000)

        if mixed:
            mixed = _crossfade(mixed, norm, crossfade_samples)
        else:
            mixed = norm

        # Silence pad after segment (except after last)
        if idx < len(segments) - 1:
            pad_samples = int(target_rate * seg.pause_after_ms / 1000) * target_channels
            mixed.extend(_silence(pad_samples))

        segment_reports.append({
            "index": idx,
            "speaker": seg.speaker,
            "duration_ms": duration_ms,
            "pause_after_ms": seg.pause_after_ms if idx < len(segments) - 1 else 0,
        })

    total_ms = int(len(mixed) / (target_rate * target_channels) * 1000)
    out_wav = _write_wav(mixed, target_channels, target_width, target_rate)
    report = {
        "segment_count": len(segments),
        "total_duration_ms": total_ms,
        "target_sample_rate": target_rate,
        "target_channels": target_channels,
        "crossfade_ms": crossfade_ms,
        "segments": segment_reports,
    }
    return out_wav, report


def mix_podcast(*, title: str, segments: list[dict]) -> dict:
    """Legacy stub kept for backward compatibility — returns status only."""
    return {
        "status": "ok",
        "title": title,
        "segment_count": len(segments),
    }
