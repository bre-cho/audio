def test_baselines_create_transition_and_active(client):
    create = client.post(
        "/api/v1/baselines",
        json={
            "artifact_id": "artifact-1",
            "baseline_type": "canary",
            "owner": "qa",
            "approved_by": "lead",
            "drift_budget_policy": "default-budget",
        },
    )
    assert create.status_code == 200
    baseline_id = create.json()["baseline_id"]

    transition_canary = client.post(
        f"/api/v1/baselines/{baseline_id}/transition",
        json={"lifecycle_state": "canary_active"},
    )
    assert transition_canary.status_code == 200
    assert transition_canary.json()["lifecycle_state"] == "canary_active"

    transition_active = client.post(
        f"/api/v1/baselines/{baseline_id}/transition",
        json={"lifecycle_state": "active"},
    )
    assert transition_active.status_code == 200
    assert transition_active.json()["status"] == "active"

    active = client.get("/api/v1/baselines/active/canary")
    assert active.status_code == 200
    assert active.json()["baseline_id"] == baseline_id


def test_baselines_canary_evaluation_and_risk_tools(client):
    evaluate = client.post(
        "/api/v1/baselines/canary/evaluate",
        json={
            "confidence_score": 65,
            "sample_size": 120,
            "segment_coverage_ok": True,
        },
    )
    assert evaluate.status_code == 200
    assert evaluate.json()["action"] == "rollback"
    assert evaluate.json()["rollback_required"] is True

    rollback = client.post(
        "/api/v1/baselines/segment-rollback",
        json={
            "segment_key": "provider=internal_genvoice",
            "critical": False,
        },
    )
    assert rollback.status_code == 200
    assert rollback.json()["action"] == "segment_freeze_and_fallback"

    blast = client.post(
        "/api/v1/baselines/blast-radius",
        json={
            "affected_projects": 200,
            "affected_jobs": 100,
            "affected_artifacts": 60,
            "affected_users": 90,
            "affected_publish_queue": 25,
        },
    )
    assert blast.status_code == 200
    assert blast.json()["level"] in {"high", "critical"}
