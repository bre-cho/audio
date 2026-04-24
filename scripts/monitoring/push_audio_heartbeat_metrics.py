#!/usr/bin/env python3
import argparse
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description='Write heartbeat metrics for audio synthetic probe.')
    parser.add_argument('--output', required=True, help='Output .prom file path')
    parser.add_argument('--preview-ok', action='store_true', help='Mark preview heartbeat as success')
    parser.add_argument('--narration-ok', action='store_true', help='Mark narration heartbeat as success')
    args = parser.parse_args()

    now = int(time.time())
    preview_ts = now if args.preview_ok else 0
    narration_ts = now if args.narration_ok else 0

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        '\n'.join(
            [
                '# HELP audio_preview_last_success_timestamp_seconds Last successful preview synthetic probe timestamp.',
                '# TYPE audio_preview_last_success_timestamp_seconds gauge',
                f'audio_preview_last_success_timestamp_seconds {preview_ts}',
                '# HELP audio_narration_last_success_timestamp_seconds Last successful narration synthetic probe timestamp.',
                '# TYPE audio_narration_last_success_timestamp_seconds gauge',
                f'audio_narration_last_success_timestamp_seconds {narration_ts}',
            ]
        )
        + '\n',
        encoding='utf-8',
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
