def parse_speaker_script(raw_script: str) -> list[dict[str, str]]:
    lines: list[dict[str, str]] = []
    for raw in raw_script.splitlines():
        raw = raw.strip()
        if not raw or ':' not in raw:
            continue
        speaker, text = raw.split(':', 1)
        lines.append({'speaker': speaker.strip(), 'text': text.strip()})
    return lines
