class SpeakerSimilarityService:
    def score(self, source_path: str, converted_path: str) -> float:
        # Wire ECAPA-TDNN / SpeechBrain / provider similarity here.
        raise NotImplementedError("Speaker similarity model is not wired")
