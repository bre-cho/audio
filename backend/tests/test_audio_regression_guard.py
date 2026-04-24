import json
from pathlib import Path


def test_audio_regression_cases_load():
    """Seed file must be loadable and every case must have required keys."""
    path = Path(__file__).parent / "fixtures" / "audio_regression_cases.json"
    cases = json.loads(path.read_text())

    assert cases, "regression case list must not be empty"
    assert all("id" in case for case in cases), "every case must have an 'id'"
    assert all("input" in case for case in cases), "every case must have an 'input'"
    assert all("expected" in case for case in cases), "every case must have an 'expected'"


def test_audio_preview_basic_contract(client):
    """POST /api/v1/audio/preview must return a valid job envelope."""
    res = client.post(
        "/api/v1/audio/preview",
        json={"text": "hello world", "voice": "default"},
    )

    # endpoint currently returns 201 Created; allow 200/201/202 for forward-compat
    assert res.status_code in (200, 201, 202), f"unexpected status {res.status_code}: {res.text}"

    body = res.json()
    assert body.get("job_id"), "response must include job_id"
    assert body.get("status") in ("queued", "processing", "succeeded"), (
        f"unexpected status value: {body.get('status')}"
    )


def test_audio_job_artifact_contract_shape(client):
    """When a job reaches 'succeeded', artifact URLs must follow the expected path scheme."""
    res = client.post(
        "/api/v1/audio/preview",
        json={"text": "hello world", "voice": "default"},
    )
    body = res.json()

    assert "job_id" in body, "response must include job_id"
    assert "status" in body, "response must include status"

    if body["status"] == "succeeded":
        assert body["preview_url"].startswith("/artifacts/audio/"), (
            f"preview_url has wrong prefix: {body['preview_url']}"
        )
        assert body["output_url"].startswith("/artifacts/audio/"), (
            f"output_url has wrong prefix: {body['output_url']}"
        )
