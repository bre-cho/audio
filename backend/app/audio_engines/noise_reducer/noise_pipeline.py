from __future__ import annotations

import array
import io
import math
import struct
import wave

# ---------------------------------------------------------------------------
# Frame-based RMS noise gate (pure Python, no external deps)
# Algorithm:
#   1. Estimate noise floor RMS from the first `noise_profile_ms` of audio.
#   2. For each overlapping frame, compute RMS.
#   3. Compute per-sample gain: 1.0 above gate threshold, attenuated below.
#   4. Apply gain with linear cross-fade between frames.
# ---------------------------------------------------------------------------

_FRAME_MS = 20  # frame size in milliseconds
_MIN_GAIN = 0.05  # never fully silence — avoids digital artifacts

NOISE_PROFILES: dict[str, dict[str, float]] = {
    "balanced": {"threshold_scale": 2.0, "min_gain": 0.06, "frame_ms": 20},
    "narration": {"threshold_scale": 2.4, "min_gain": 0.04, "frame_ms": 24},
    "podcast": {"threshold_scale": 1.8, "min_gain": 0.08, "frame_ms": 20},
    "livestream": {"threshold_scale": 1.4, "min_gain": 0.12, "frame_ms": 16},
}


def _resolve_noise_profile(voice_profile: str) -> dict[str, float]:
    return NOISE_PROFILES.get(voice_profile, NOISE_PROFILES["balanced"])


def _read_wav(data: bytes) -> tuple[array.array, int, int, int]:
    """Return (samples_signed, nchannels, sampwidth, framerate)."""
    with wave.open(io.BytesIO(data), "rb") as wf:
        nchannels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        raw = wf.readframes(wf.getnframes())

    if sampwidth == 1:
        samples: list[int] = [b - 128 for b in raw]
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


def _rms(samples: list[int]) -> float:
    if not samples:
        return 0.0
    return math.sqrt(sum(s * s for s in samples) / len(samples))


def reduce_noise_wav(
    *,
    input_wav: bytes,
    strength: float = 0.65,
    noise_profile_ms: int = 300,
    voice_profile: str = "balanced",
) -> tuple[bytes, dict]:
    """Apply spectral noise gate to a WAV.

    Returns (output_wav_bytes, report_dict).
    """
    strength = max(0.0, min(1.0, strength))
    profile_cfg = _resolve_noise_profile(voice_profile)
    samples, nchannels, sampwidth, framerate = _read_wav(input_wav)

    # Flatten to mono-equivalent for gain computation (still process all channels)
    frame_ms = int(profile_cfg["frame_ms"])
    frame_size = max(1, int(framerate * frame_ms / 1000)) * nchannels
    noise_samples = math.ceil(framerate * noise_profile_ms / 1000) * nchannels
    noise_floor = _rms(samples[:noise_samples]) if samples else 0.0
    gate_threshold = noise_floor * (1.0 + strength * float(profile_cfg["threshold_scale"]))
    min_gain = float(profile_cfg["min_gain"])

    # Build per-sample gains
    gains: list[float] = []
    for frame_start in range(0, len(samples), frame_size):
        frame = samples[frame_start : frame_start + frame_size]
        frame_rms = _rms(frame)
        if frame_rms >= gate_threshold or gate_threshold == 0:
            g = 1.0
        else:
            ratio = frame_rms / gate_threshold if gate_threshold > 0 else 0.0
            g = max(min_gain, min_gain + (1.0 - min_gain) * ratio * (1.0 - strength))
        gains.extend([g] * len(frame))

    # Apply gains with linear interpolation between frame boundaries to
    # avoid clicks at frame edges.
    prev_g = gains[0] if gains else 1.0
    output: list[int] = []
    interp_window = max(1, frame_size // 4)
    for i, s in enumerate(samples):
        g = gains[i] if i < len(gains) else 1.0
        # Blend toward new gain over interp_window samples
        t = (i % frame_size) / interp_window if frame_size > 0 else 1.0
        blended = prev_g + min(1.0, t) * (g - prev_g)
        if i % frame_size == 0:
            prev_g = g
        output.append(int(s * blended))

    out_wav = _write_wav(output, nchannels, sampwidth, framerate)
    reduced_frames = sum(1 for g in gains if g < 0.5)
    report = {
        "voice_profile": voice_profile if voice_profile in NOISE_PROFILES else "balanced",
        "noise_floor_rms": round(noise_floor, 2),
        "gate_threshold": round(gate_threshold, 2),
        "frames_attenuated": reduced_frames,
        "total_frames": len(gains) // max(1, frame_size),
        "strength_applied": strength,
        "frame_ms": frame_ms,
    }
    return out_wav, report


def reduce_noise(*, input_artifact_id: str, strength: float = 0.65) -> dict:
    """Legacy stub kept for backward compatibility — returns status only."""
    return {
        "status": "ok",
        "input_artifact_id": input_artifact_id,
        "strength": strength,
    }
