from __future__ import annotations
import os
import httpx
from .errors import ElevenLabsAuthError, map_http_error

class ElevenLabsClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.elevenlabs.io"):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(
            connect=float(os.getenv("ELEVENLABS_CONNECT_TIMEOUT", "10")),
            read=float(os.getenv("ELEVENLABS_READ_TIMEOUT", "120")),
            write=60,
            pool=10,
        )

    @property
    def headers(self) -> dict[str, str]:
        return {"xi-api-key": self.api_key}

    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        if not self.api_key:
            raise ElevenLabsAuthError("ELEVENLABS_API_KEY is missing")
        url = f"{self.base_url}{path}"
        headers = dict(self.headers)
        headers.update(kwargs.pop("headers", {}) or {})
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.request(method, url, headers=headers, **kwargs)
        if resp.status_code >= 400:
            raise map_http_error(resp.status_code, resp.text[:1000])
        return resp

    def stream(self, method: str, path: str, **kwargs):
        if not self.api_key:
            raise ElevenLabsAuthError("ELEVENLABS_API_KEY is missing")
        url = f"{self.base_url}{path}"
        headers = dict(self.headers)
        headers.update(kwargs.pop("headers", {}) or {})
        return httpx.stream(method, url, headers=headers, timeout=self.timeout, **kwargs)
