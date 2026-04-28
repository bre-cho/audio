from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.core.config import settings


def test_storage_health_local_probe(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "storage_backend", "local")
    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path))

    response = client.get("/api/v1/storage/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["backend"] == "local"

    probe_key = body["probe_key"]
    probe_path = tmp_path / probe_key
    # Local probe must be cleaned up by the endpoint.
    assert not Path(probe_path).exists()


def test_storage_health_s3_probe_if_configured(client, monkeypatch):
    s3_bucket = os.getenv("S3_BUCKET")
    if not s3_bucket:
        pytest.skip("S3 probe skipped: S3_BUCKET is not configured")

    monkeypatch.setattr(settings, "storage_backend", "s3")
    monkeypatch.setattr(settings, "s3_bucket", s3_bucket)
    monkeypatch.setattr(settings, "s3_region", os.getenv("S3_REGION"))
    monkeypatch.setattr(settings, "s3_endpoint_url", os.getenv("S3_ENDPOINT_URL"))
    monkeypatch.setattr(settings, "s3_public_base_url", os.getenv("S3_PUBLIC_BASE_URL"))

    response = client.get("/api/v1/storage/health")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "ok"
    assert body["backend"] == "s3"
    assert body["s3_bucket"] == s3_bucket
    assert body["probe_key"].startswith("_healthcheck/")
