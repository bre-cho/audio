from __future__ import annotations

from pathlib import Path


def main() -> int:
    app_ts = Path("frontend/src/api.ts").read_text(encoding="utf-8")
    required = [
        "providerHealth",
        "audioCapabilities",
        "ttsGenerate",
        "generateConversation",
    ]
    missing = [name for name in required if name not in app_ts]
    if missing:
        raise SystemExit(f"missing frontend api methods: {missing}")
    Path("artifacts/verify").mkdir(parents=True, exist_ok=True)
    with Path("artifacts/verify/audio_production_verify_report.txt").open("a", encoding="utf-8") as fp:
        fp.write("[verify_frontend_api_parity] ok\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
