from app.core.storage import StorageService
from app.core.config import settings


class _FakeS3Client:
    def __init__(self) -> None:
        self.calls = []

    def put_object(self, **kwargs):
        self.calls.append(kwargs)


def test_storage_service_local_put_bytes(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "storage_backend", "local")

    svc = StorageService(root_dir=tmp_path)
    stored = svc.put_bytes("audio/sample.wav", b"demo-bytes", "audio/wav")

    assert stored.key == "audio/sample.wav"
    assert stored.public_url == "/artifacts/audio/sample.wav"
    assert stored.path == str(tmp_path / "audio/sample.wav")
    assert stored.size_bytes == len(b"demo-bytes")
    assert (tmp_path / "audio/sample.wav").read_bytes() == b"demo-bytes"


def test_storage_service_s3_put_bytes(monkeypatch):
    monkeypatch.setattr(settings, "storage_backend", "s3")
    monkeypatch.setattr(settings, "s3_bucket", "audio-assets-prod")
    monkeypatch.setattr(settings, "s3_public_base_url", "https://cdn.example.com/audio")

    fake = _FakeS3Client()
    svc = StorageService()
    monkeypatch.setattr(svc, "_build_s3_client", lambda: fake)

    stored = svc.put_bytes("voice-clone/samples/demo.wav", b"sample-data", "audio/wav")

    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert call["Bucket"] == "audio-assets-prod"
    assert call["Key"] == "voice-clone/samples/demo.wav"
    assert call["Body"] == b"sample-data"
    assert call["ContentType"] == "audio/wav"
    assert call["Metadata"]["sha256"] == stored.checksum

    assert stored.key == "voice-clone/samples/demo.wav"
    assert stored.path == "s3://audio-assets-prod/voice-clone/samples/demo.wav"
    assert stored.public_url == "https://cdn.example.com/audio/voice-clone/samples/demo.wav"
    assert stored.size_bytes == len(b"sample-data")
