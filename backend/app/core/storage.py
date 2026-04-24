from dataclasses import dataclass


@dataclass
class StoredObject:
    key: str
    public_url: str | None = None


class StorageService:
    def put_bytes(self, key: str, data: bytes, content_type: str) -> StoredObject:
        return StoredObject(key=key, public_url=None)
