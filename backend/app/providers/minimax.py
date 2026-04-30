from app.providers.base import BaseTTSProvider


class MinimaxProvider(BaseTTSProvider):
    code = 'minimax'

    def list_voices(self, filters: dict | None = None) -> list[dict]:
        return []

    def generate_speech(self, payload: dict) -> dict:
        del payload
        raise NotImplementedError('Minimax generate_speech is not implemented yet')

    def clone_voice(self, payload: dict) -> dict:
        del payload
        raise NotImplementedError('Minimax clone_voice is not implemented yet')
