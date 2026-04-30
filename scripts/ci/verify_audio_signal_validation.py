from __future__ import annotations

from pathlib import Path

from app.services.audio_quality.audio_signal_validator import validate_wav_signal


def main() -> int:
    report = validate_wav_signal(b"not-a-wav")
    if report.passed:
        raise SystemExit("invalid wav should fail")
    Path("artifacts/verify").mkdir(parents=True, exist_ok=True)
    with Path("artifacts/verify/audio_production_verify_report.txt").open("a", encoding="utf-8") as fp:
        fp.write("[verify_audio_signal_validation] ok\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
