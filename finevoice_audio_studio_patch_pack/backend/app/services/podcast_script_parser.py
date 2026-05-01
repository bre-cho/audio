from dataclasses import dataclass


@dataclass(frozen=True)
class PodcastLine:
    speaker: str
    text: str


class PodcastScriptParser:
    def parse(self, script: str) -> list[PodcastLine]:
        lines: list[PodcastLine] = []
        for raw in script.splitlines():
            if ":" not in raw:
                continue
            speaker, text = raw.split(":", 1)
            if speaker.strip() and text.strip():
                lines.append(PodcastLine(speaker=speaker.strip(), text=text.strip()))
        if not lines:
            raise ValueError("Podcast script must contain SPEAKER: text lines")
        return lines
