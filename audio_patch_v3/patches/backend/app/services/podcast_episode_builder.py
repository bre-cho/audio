from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class PodcastEpisodePlan:
    title: str
    speakers: list[str]
    segments: list[dict]
    requires_tts: bool
    requires_mixdown: bool

    def dict(self) -> dict:
        return asdict(self)


class PodcastEpisodeBuilder:
    def build_plan(self, *, title: str, script: str, speakers: list[str] | None = None) -> PodcastEpisodePlan:
        speakers = speakers or ["Host"]
        segments = []
        for i, line in enumerate([x.strip() for x in script.splitlines() if x.strip()]):
            speaker = speakers[i % len(speakers)]
            if ":" in line:
                maybe_speaker, text = line.split(":", 1)
                speaker = maybe_speaker.strip() or speaker
                line = text.strip()
            segments.append({"index": i, "speaker": speaker, "text": line})
        if not segments:
            raise ValueError("podcast_script_empty")
        return PodcastEpisodePlan(title=title, speakers=speakers, segments=segments, requires_tts=True, requires_mixdown=True)
