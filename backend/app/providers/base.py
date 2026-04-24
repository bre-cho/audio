from abc import ABC, abstractmethod


class BaseTTSProvider(ABC):
    code: str

    @abstractmethod
    def list_voices(self, filters: dict | None = None) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def generate_speech(self, payload: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def clone_voice(self, payload: dict) -> dict:
        raise NotImplementedError
