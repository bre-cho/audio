from __future__ import annotations

from app.services.tts_generation_service import TTSGenerationService


class PodcastTTSOrchestrator:
    def __init__(self, output_dir: str = "artifacts/podcast/segments"):
        self._output_dir = output_dir
        self._tts = TTSGenerationService()

    def synthesize_segments(self, episode_plan: dict, speaker_voice_map: dict[str, str]) -> list[dict]:
        """Synthesize TTS audio for every segment in an episode plan.

        Returns the same segments list enriched with ``audio_path`` and
        ``decoded_wav_path`` keys.
        """
        results: list[dict] = []
        for seg in episode_plan.get("segments", []):
            voice_id = speaker_voice_map.get(seg["speaker"])
            if not voice_id:
                raise ValueError(f"no_voice_assigned_for_speaker:{seg['speaker']}")
            tts_result = self._tts.generate(
                text=seg["text"],
                voice_id=voice_id,
                output_dir=self._output_dir,
            )
            results.append({
                **seg,
                "audio_path": tts_result["audio_path"],
                "decoded_wav_path": tts_result["decoded_wav_path"],
                "provider": tts_result["provider"],
            })
        return results
