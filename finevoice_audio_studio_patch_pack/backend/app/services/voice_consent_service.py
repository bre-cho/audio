from dataclasses import dataclass


@dataclass(frozen=True)
class ConsentRecord:
    subject_id: str
    granted: bool
    purpose: str
    evidence_uri: str | None = None


class VoiceConsentService:
    def assert_consent(self, record: ConsentRecord) -> None:
        if not record.granted:
            raise PermissionError("Voice cloning requires explicit consent")
        if not record.purpose:
            raise ValueError("Consent purpose is required")
