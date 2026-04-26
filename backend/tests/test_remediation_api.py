def test_remediation_create_and_list(client):
    create = client.post(
        "/api/v1/remediation",
        json={
            "trigger_source": "incident",
            "runbook_id": "rb-1",
            "action_plan": [{"step": "freeze"}],
            "risk_level": "low",
            "blast_radius_estimate": "low",
            "confidence_score": 92,
            "auto_apply_allowed": True,
        },
    )
    assert create.status_code == 200
    body = create.json()
    assert body["approval_tier"] == "tier_0"
    assert body["execution_allowed"] is True

    listed = client.get("/api/v1/remediation")
    assert listed.status_code == 200
    assert any(row["remediation_id"] == body["remediation_id"] for row in listed.json())


def test_remediation_high_risk_is_blocked(client):
    create = client.post(
        "/api/v1/remediation",
        json={
            "trigger_source": "regression",
            "runbook_id": "rb-2",
            "action_plan": [{"step": "rollback"}],
            "risk_level": "high",
            "blast_radius_estimate": "high",
            "confidence_score": 95,
            "auto_apply_allowed": True,
        },
    )
    assert create.status_code == 200
    body = create.json()
    assert body["approval_tier"] == "tier_2"
    assert body["execution_allowed"] is False
