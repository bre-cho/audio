from __future__ import annotations

import io
import math
import struct
import wave

# ---------------------------------------------------------------------------
# Voice Enhancement Pipeline — pure Python (no external deps)
# Stages per preset:
#   clean     : dc_block → normalize
#   broadcast : dc_block → high_pass → normalize → compress → normalize
#   podcast   : dc_block → normalize → compress
# ---------------------------------------------------------------------------

PRESETS: dict[str, list[str]] = {
    "clean": ["dc_block", "normalize"],
    "broadcast": ["dc_block", "high_pass", "normalize", "compress", "normalize"],
    "podcast": ["dc_block", "normalize", "compress"],
}
_DEFAULT_PRESET = "clean"

VOICE_PROFILES: dict[str, dict[str, float]] = {
    "balanced": {
        "high_pass_cutoff": 80.0,
        "normalize_peak_ratio": 0.90,
        "compress_threshold_ratio": 0.50,
        "compress_ratio": 4.0,
        "attack_ms": 5.0,
        "release_ms": 50.0,
    },
    "warm": {
        "high_pass_cutoff": 65.0,
        "normalize_peak_ratio": 0.88,
        "compress_threshold_ratio": 0.56,
        "compress_ratio": 3.0,
        "attack_ms": 8.0,
        "release_ms": 80.0,
    },
    "bright": {
        "high_pass_cutoff": 95.0,
        "normalize_peak_ratio": 0.92,
        "compress_threshold_ratio": 0.46,
        "compress_ratio": 4.5,
        "attack_ms": 3.0,
        "release_ms": 45.0,
    },
    "broadcast": {
        "high_pass_cutoff": 110.0,
        "normalize_peak_ratio": 0.94,
        "compress_threshold_ratio": 0.42,
        "compress_ratio": 5.0,
        "attack_ms": 2.5,
        "release_ms": 70.0,
    },
}


def _resolve_voice_profile(voice_profile: str) -> dict[str, float]:
    return VOICE_PROFILES.get(voice_profile, VOICE_PROFILES["balanced"])


# --- WAV I/O ----------------------------------------------------------------

def _read_wav(data: bytes) -> tuple[list[int], int, int, int]:
    with wave.open(io.BytesIO(data), "rb") as wf:
        nchannels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    if sampwidth == 1:
        samples = [b - 128 for b in raw]
    elif sampwidth == 2:
        count = len(raw) // 2
        samples = list(struct.unpack(f"<{count}h", raw[: count * 2]))
    else:
        raise ValueError(f"unsupported sample width: {sampwidth}")
    return samples, nchannels, sampwidth, framerate


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


# --- Processing stages ------------------------------------------------------

def _dc_block(samples: list[int]) -> list[int]:
    """Remove DC offset by subtracting mean."""
    if not samples:
        return samples
    mean = sum(samples) / len(samples)
    return [int(s - mean) for s in samples]


def _high_pass(samples: list[int], cutoff_hz: float = 80.0, framerate: int = 44100) -> list[int]:
    """Single-pole IIR high-pass filter to remove rumble below cutoff_hz."""
    rc = 1.0 / (2.0 * math.pi * cutoff_hz)
    dt = 1.0 / framerate
    alpha = rc / (rc + dt)
    out: list[int] = []
    prev_x = float(samples[0]) if samples else 0.0
    prev_y = 0.0
    for x in samples:
        y = alpha * (prev_y + x - prev_x)
        out.append(int(y))
        prev_x = float(x)
        prev_y = y
    return out


def _normalize(samples: list[int], sampwidth: int, target_peak_ratio: float = 0.9) -> list[int]:
    """Peak normalize to target_peak_ratio of full scale."""
    if not samples:
        return samples
    max_val = 127 if sampwidth == 1 else 32767
    peak = max(abs(s) for s in samples)
    if peak == 0:
        return samples
    gain = (max_val * target_peak_ratio) / peak
    return [int(s * gain) for s in samples]


def _compress(
    samples: list[int],
    sampwidth: int,
    threshold_ratio: float = 0.5,
    ratio: float = 4.0,
    attack_ms: float = 5.0,
    release_ms: float = 50.0,
    framerate: int = 44100,
) -> list[int]:
    """Soft-knee compressor with attack/release envelope."""
    max_val = 127 if sampwidth == 1 else 32767
    threshold = max_val * threshold_ratio
    attack_coef = math.exp(-1.0 / (framerate * attack_ms / 1000.0))
    release_coef = math.exp(-1.0 / (framerate * release_ms / 1000.0))
    envelope = 0.0
    out: list[int] = []
    for s in samples:
        level = abs(s)
        if level > envelope:
            envelope = attack_coef * envelope + (1.0 - attack_coef) * level
        else:
            envelope = release_coef * envelope + (1.0 - release_coef) * level
        if envelope > threshold and threshold > 0:
            gain_reduction = threshold + (envelope - threshold) / ratio
            gain = gain_reduction / envelope
        else:
            gain = 1.0
        out.append(int(s * gain))
    return out


# --- Public API -------------------------------------------------------------

def enhance_voice_wav(
    *,
    input_wav: bytes,
    preset: str = _DEFAULT_PRESET,
    voice_profile: str = "balanced",
) -> tuple[bytes, dict]:
    """Enhance a WAV through the preset pipeline.

    Returns (output_wav_bytes, report_dict).
    """
    resolved_preset = preset if preset in PRESETS else _DEFAULT_PRESET
    resolved_profile = voice_profile if voice_profile in VOICE_PROFILES else "balanced"
    profile_cfg = _resolve_voice_profile(voice_profile)
    stages = PRESETS[resolved_preset]
    samples, nchannels, sampwidth, framerate = _read_wav(input_wav)
    applied: list[str] = []

    for stage in stages:
        if stage == "dc_block":
            samples = _dc_block(samples)
        elif stage == "high_pass":
            samples = _high_pass(samples, cutoff_hz=profile_cfg["high_pass_cutoff"], framerate=framerate)
        elif stage == "normalize":
            samples = _normalize(samples, sampwidth, target_peak_ratio=profile_cfg["normalize_peak_ratio"])
        elif stage == "compress":
            samples = _compress(
                samples,
                sampwidth,
                threshold_ratio=profile_cfg["compress_threshold_ratio"],
                ratio=profile_cfg["compress_ratio"],
                attack_ms=profile_cfg["attack_ms"],
                release_ms=profile_cfg["release_ms"],
                framerate=framerate,
            )
        applied.append(stage)

    out_wav = _write_wav(samples, nchannels, sampwidth, framerate)
    peak_out = max((abs(s) for s in samples), default=0)
    max_val = 127 if sampwidth == 1 else 32767
    report = {
        "preset_requested": preset,
        "preset_resolved": resolved_preset,
        "voice_profile_requested": voice_profile,
        "voice_profile_resolved": resolved_profile,
        "stages_applied": applied,
        "peak_out": peak_out,
        "peak_out_dbfs": round(20 * math.log10(peak_out / max_val), 2) if peak_out > 0 else -120.0,
    }
    return out_wav, report


def enhance_voice(*, input_artifact_id: str, preset: str) -> dict:
    """Legacy stub kept for backward compatibility — returns status only."""
    return {
        "status": "ok",
        "input_artifact_id": input_artifact_id,
        "preset": preset,
    }
