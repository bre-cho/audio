class SpeakerCastingService:
    def cast(self, speaker_names: list[str], voice_map: dict[str, str]) -> dict[str, str]:
        missing = [name for name in speaker_names if name not in voice_map]
        if missing:
            raise ValueError(f"Missing voice assignment for speakers: {missing}")
        return {name: voice_map[name] for name in speaker_names}
