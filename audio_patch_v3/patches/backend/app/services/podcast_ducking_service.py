from __future__ import annotations


class PodcastDuckingService:
    def apply_ducking(self, voice_track_path: str, bgm_path: str, output_path: str) -> str:
        raise NotImplementedError("Wire ffmpeg sidechaincompress ducking before enabling BGM podcast mix")
