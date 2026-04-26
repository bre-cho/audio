from app.core.config import settings
from app.providers.elevenlabs import ElevenLabsProvider
from app.providers.minimax import MinimaxProvider
from app.providers.internal_genvoice import InternalGenVoiceProvider


class ProviderRouter:
    def resolve(self, provider_code: str | None = None):
        provider_code = provider_code or settings.default_provider
        if provider_code == 'elevenlabs':
            return ElevenLabsProvider()
        if provider_code == 'minimax':
            return MinimaxProvider()
        if provider_code == 'internal_genvoice':
            return InternalGenVoiceProvider()
        raise ValueError(f'Nha cung cap khong duoc ho tro: {provider_code}')
