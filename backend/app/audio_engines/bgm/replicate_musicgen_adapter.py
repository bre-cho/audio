from __future__ import annotations

import os
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from app.services.audio_signal_validator import validate_audio_signal

# Only accept output URLs from trusted Replicate CDN domains
_TRUSTED_URL_RE = re.compile(
    r"^https://(?:replicate\.delivery|pbxt\.replicate\.delivery|[a-z0-9\-]+\.replicate\.delivery)/",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class BGMResult:
    output_path: str
    provider: str
    prompt: str
    duration_sec: float
    loopable: bool
    license: dict


class ReplicateMusicGenAdapter:
    provider_name = "replicate_musicgen"

    # Pinned public model version — update when a newer version is preferred.
    MODEL_VERSION = "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb"

    def generate(self, *, prompt: str, duration_sec: float, loopable: bool, output_path: str, **kwargs) -> BGMResult:
        api_token = os.getenv("REPLICATE_API_TOKEN")
        if not api_token:
            raise RuntimeError("missing_replicate_api_token: set REPLICATE_API_TOKEN")
        try:
            import replicate  # type: ignore
        except ImportError as exc:
            raise RuntimeError("replicate_sdk_missing: add 'replicate' to requirements.txt") from exc

        output = replicate.run(
            self.MODEL_VERSION,
            input={
                "prompt": prompt,
                "duration": int(duration_sec),
                "continuation": False,
                "normalization_strategy": "peak",
                "output_format": "wav",
            },
        )
        # replicate.run returns a URL or file-like — normalise to URL string
        audio_url = str(output) if not hasattr(output, "read") else None
        if audio_url is None:
            # file-like object
            audio_bytes = output.read()
        else:
            if not _TRUSTED_URL_RE.match(audio_url):
                raise RuntimeError(f"replicate_musicgen_untrusted_output_url: {audio_url!r}")
            with urllib.request.urlopen(audio_url, timeout=120) as resp:
                audio_bytes = resp.read()

        if not audio_bytes:
            raise RuntimeError("replicate_musicgen_returned_empty_audio")

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(audio_bytes)

        signal = validate_audio_signal(str(out))
        if not signal.ok:
            raise RuntimeError(f"replicate_musicgen_invalid_audio:{signal.reason}")

        return BGMResult(
            output_path=str(out),
            provider=self.provider_name,
            prompt=prompt,
            duration_sec=signal.duration_sec,
            loopable=loopable,
            license={
                "type": "research_non_commercial",
                "source": "meta/musicgen via replicate",
                "note": "Verify commercial licensing before production use",
            },
        )
