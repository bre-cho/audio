from app.schemas.billing import UsageEstimateOut


class CreditPolicy:
    TTS_PER_100_CHARS = 1
    CONVERSATION_SEGMENT_FEE = 2
    CLONE_JOB_FEE = 1000

    @classmethod
    def estimate_tts(cls, chars: int) -> UsageEstimateOut:
        credits = max(1, (chars + 99) // 100)
        return UsageEstimateOut(units=chars, unit_type='chars', estimated_credits=credits)
