from __future__ import annotations

from pathlib import Path

try:
    from app.audio_engines.qa.audio_quality_metrics import analyze_audio_quality
except Exception:
    analyze_audio_quality = None


class AudioEnhancementQualityService:
    def before_after_report(self, before_path: str, after_path: str) -> dict:
        if not Path(before_path).exists() or not Path(after_path).exists():
            raise RuntimeError("before_or_after_audio_missing")
        before = analyze_audio_quality(before_path) if analyze_audio_quality else {"available": False}
        after = analyze_audio_quality(after_path) if analyze_audio_quality else {"available": False}
        return {
            "before": before,
            "after": after,
            "improved": self._is_improved(before, after),
        }

    def _is_improved(self, before: dict, after: dict) -> bool:
        if not before or not after or before.get("available") is False:
            return False
        before_clip = before.get("clipping_detected", False)
        after_clip = after.get("clipping_detected", False)
        before_silence = before.get("silence_ratio", 1)
        after_silence = after.get("silence_ratio", 1)
        return (not after_clip or before_clip) and after_silence <= before_silence
