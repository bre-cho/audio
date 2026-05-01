from __future__ import annotations


class PodcastTTSOrchestrator:
    def synthesize_segments(self, episode_plan: dict, speaker_voice_map: dict[str, str]) -> list[dict]:
        raise NotImplementedError("Wire TTSGenerationService per podcast segment before enabling full podcast generation")
