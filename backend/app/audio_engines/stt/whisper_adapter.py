from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass(frozen=True)
class TranscriptSegment:
    start: float
    end: float
    text: str
    confidence: float | None = None


@dataclass(frozen=True)
class TranscriptResult:
    language: str | None
    text: str
    segments: list[TranscriptSegment]

    def dict(self) -> dict:
        return {"language": self.language, "text": self.text, "segments": [asdict(s) for s in self.segments]}


class WhisperAdapter:
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name

    def transcribe(self, audio_path: str) -> TranscriptResult:
        p = Path(audio_path)
        if not p.exists() or p.stat().st_size == 0:
            raise ValueError("audio_file_missing_or_empty")
        try:
            import whisper  # type: ignore
        except Exception as exc:
            raise RuntimeError("whisper_dependency_missing: install openai-whisper or switch STT_PROVIDER") from exc
        model = whisper.load_model(self.model_name)
        raw = model.transcribe(str(p))
        segments = [TranscriptSegment(float(s["start"]), float(s["end"]), s["text"].strip()) for s in raw.get("segments", [])]
        return TranscriptResult(raw.get("language"), raw.get("text", "").strip(), segments)
