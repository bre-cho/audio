from app.providers.base import BaseTTSProvider


class InternalGenVoiceProvider(BaseTTSProvider):
    code = 'internal_genvoice'

    def list_voices(self, filters: dict | None = None) -> list[dict]:
        return []

    def generate_speech(self, payload: dict) -> dict:
        return {'status': 'not_implemented', 'provider': self.code}

    def clone_voice(self, payload: dict) -> dict:
        return {'status': 'not_implemented', 'provider': self.code}
