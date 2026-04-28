from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

from app.core.config import settings
from app.core.storage import StorageService


def test_storage_local_get_and_delete(tmp_path: Path):
    storage = StorageService(root_dir=tmp_path)
    stored = storage.put_bytes('x/test.wav', b'RIFFdemo', 'audio/wav')

    data = storage.get_bytes(stored.key)
    assert data == b'RIFFdemo'

    deleted = storage.delete(stored.key)
    assert deleted is True
    assert storage.delete(stored.key) is False


def test_storage_s3_get_and_delete_with_mock(monkeypatch):
    # Configure S3 mode
    monkeypatch.setattr(settings, 'storage_backend', 's3', raising=False)
    monkeypatch.setattr(settings, 's3_bucket', 'unit-test-bucket', raising=False)
    monkeypatch.setattr(settings, 's3_endpoint_url', 'http://minio:9000', raising=False)

    client = Mock()
    client.get_object.return_value = {'Body': Mock(read=Mock(return_value=b's3-bytes'))}

    storage = StorageService()
    monkeypatch.setattr(storage, '_build_s3_client', lambda: client)

    data = storage.get_bytes('abc/file.wav')
    assert data == b's3-bytes'
    client.get_object.assert_called_once_with(Bucket='unit-test-bucket', Key='abc/file.wav')

    deleted = storage.delete('abc/file.wav')
    assert deleted is True
    client.delete_object.assert_called_once_with(Bucket='unit-test-bucket', Key='abc/file.wav')
