from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpeakerSimilarityReport:
    similarity_score: float | None
    naturalness_score: float | None
    artifact_score: float | None
    reason: str


def score_speaker_similarity(reference_path: str, generated_path: str) -> SpeakerSimilarityReport:
    # Production hook: wire ECAPA-TDNN / Resemblyzer / provider similarity API.
    return SpeakerSimilarityReport(None, None, None, "similarity_engine_not_configured")
