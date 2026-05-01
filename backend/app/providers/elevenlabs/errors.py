class ElevenLabsError(RuntimeError):
    pass

class ElevenLabsAuthError(ElevenLabsError):
    pass

class ElevenLabsQuotaError(ElevenLabsError):
    pass

class ElevenLabsRateLimitError(ElevenLabsError):
    pass

class ElevenLabsValidationError(ElevenLabsError):
    pass

class ElevenLabsCapabilityError(ElevenLabsError):
    pass


def map_http_error(status_code: int, body: str) -> ElevenLabsError:
    if status_code in (401, 403):
        return ElevenLabsAuthError(f"elevenlabs_auth_failed: {body}")
    if status_code == 429:
        return ElevenLabsRateLimitError(f"elevenlabs_rate_limited: {body}")
    if status_code == 402:
        return ElevenLabsQuotaError(f"elevenlabs_quota_exceeded: {body}")
    if 400 <= status_code < 500:
        return ElevenLabsValidationError(f"elevenlabs_validation_error_{status_code}: {body}")
    return ElevenLabsError(f"elevenlabs_http_error_{status_code}: {body}")
