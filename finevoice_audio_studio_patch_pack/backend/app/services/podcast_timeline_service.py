class PodcastTimelineService:
    def build(self, parsed_lines: list, cast_map: dict[str, str]) -> list[dict]:
        timeline = []
        for idx, line in enumerate(parsed_lines):
            timeline.append({
                "index": idx,
                "speaker": line.speaker,
                "voice_id": cast_map[line.speaker],
                "text": line.text,
                "artifact_id": None,
                "start_sec": None,
                "end_sec": None,
            })
        return timeline
