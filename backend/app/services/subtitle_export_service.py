class SubtitleExportService:
    def to_srt(self, segments: list[dict]) -> str:
        blocks = []
        for i, seg in enumerate(segments, 1):
            blocks.append(f"{i}\n{self._fmt(seg['start'])} --> {self._fmt(seg['end'])}\n{seg['text']}\n")
        return "\n".join(blocks)

    def to_vtt(self, segments: list[dict]) -> str:
        return "WEBVTT\n\n" + self.to_srt(segments)

    def _fmt(self, sec: float) -> str:
        ms = int((sec - int(sec)) * 1000)
        s = int(sec) % 60
        m = (int(sec) // 60) % 60
        h = int(sec) // 3600
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
