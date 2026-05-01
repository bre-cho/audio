class STTService:
    def transcribe(self, audio_path: str, language: str = "auto") -> dict:
        raise NotImplementedError("Wire Whisper/provider STT before enabling")
