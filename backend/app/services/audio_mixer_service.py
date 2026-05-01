class AudioMixerService:
    def mix(self, voice_tracks: list[str], bgm_path: str | None, output_path: str, ducking: bool = True) -> dict:
        # Wire ffmpeg/pydub mixdown with LUFS normalization.
        raise NotImplementedError("Audio mixer is scaffold only")
