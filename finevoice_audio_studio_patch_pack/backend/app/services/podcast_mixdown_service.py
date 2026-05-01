class PodcastMixdownService:
    def render(self, timeline: list[dict], output_path: str, bgm: dict | None = None) -> dict:
        # Wire TTS per segment + ffmpeg concat + ducking + LUFS normalize.
        raise NotImplementedError("Podcast mixdown engine is scaffold only")
