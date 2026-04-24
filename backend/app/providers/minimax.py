from app.providers.base import BaseTTSProvider


class MinimaxProvider(BaseTTSProvider):
    code = 'minimax'

    def list_voices(self, filters: dict | None = None) -> list[dict]:
        return []

    def generate_speech(self, payload: dict) -> dict:
        return {'status': 'queued', 'provider': self.code}

    def clone_voice(self, payload: dict) -> dict:
        return {'status': 'queued', 'provider': self.code}
