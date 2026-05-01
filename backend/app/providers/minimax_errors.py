from __future__ import annotations

from typing import Any


class MinimaxError(RuntimeError):
    def __init__(self, message: str, *, code: int | str | None = None, retryable: bool = False, raw: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.raw = raw or {}


class MinimaxAuthError(MinimaxError):
    pass


class MinimaxRateLimitError(MinimaxError):
    pass


class MinimaxInsufficientBalanceError(MinimaxError):
    pass


class MinimaxInvalidInputError(MinimaxError):
    pass


class MinimaxDuplicateVoiceError(MinimaxError):
    pass


class MinimaxProviderUnavailable(MinimaxError):
    pass


ERROR_CODE_MAP: dict[int, tuple[type[MinimaxError], str, bool]] = {
    1002: (MinimaxRateLimitError, "Minimax rate limit exceeded", True),
    1004: (MinimaxAuthError, "Minimax request is not authorized", False),
    1008: (MinimaxInsufficientBalanceError, "Minimax account has insufficient balance", False),
    2037: (MinimaxInvalidInputError, "Voice sample duration is invalid", False),
    2039: (MinimaxDuplicateVoiceError, "Duplicate Minimax voice id", False),
    2049: (MinimaxAuthError, "Invalid Minimax API key", False),
}


def raise_for_minimax_base_resp(payload: dict[str, Any]) -> None:
    base = payload.get("base_resp") or {}
    code = base.get("status_code")
    if code in (0, "0", None):
        return
    try:
        normalized_code = int(code)
    except (TypeError, ValueError):
        normalized_code = -1
    exc_cls, msg, retryable = ERROR_CODE_MAP.get(
        normalized_code,
        (MinimaxError, f"Minimax provider error: {base.get('status_msg') or code}", False),
    )
    raise exc_cls(msg, code=normalized_code, retryable=retryable, raw=payload)


def raise_for_http_status(status_code: int, body: dict[str, Any] | None = None) -> None:
    body = body or {}
    if status_code < 400:
        return
    if status_code in (401, 403):
        raise MinimaxAuthError("Minimax authentication failed", code=status_code, retryable=False, raw=body)
    if status_code == 429:
        raise MinimaxRateLimitError("Minimax HTTP rate limit", code=status_code, retryable=True, raw=body)
    if status_code in (408, 504):
        raise MinimaxProviderUnavailable("Minimax request timeout", code=status_code, retryable=True, raw=body)
    if status_code >= 500:
        raise MinimaxProviderUnavailable("Minimax provider unavailable", code=status_code, retryable=True, raw=body)
    raise MinimaxInvalidInputError("Minimax request rejected", code=status_code, retryable=False, raw=body)
