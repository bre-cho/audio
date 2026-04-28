def test_recovery_runbook_create_list_execute(client):
    create = client.post(
        "/api/v1/recovery/runbooks",
        json={
            "title": "Rollback audio canary",
            "root_cause_hint": "drift exceeded",
            "owner": "sre",
            "verification_command": "echo ok",
            "steps": ["freeze", "rollback", "verify"],
        },
    )
    assert create.status_code == 200
    runbook_id = create.json()["runbook_id"]

    listed = client.get("/api/v1/recovery/runbooks")
    assert listed.status_code == 200
    assert any(row["runbook_id"] == runbook_id for row in listed.json())

    execute = client.post(f"/api/v1/recovery/runbooks/{runbook_id}/execute")
    assert execute.status_code == 200
    assert execute.json()["verification_status"] == "pass"


def test_recovery_drill_requires_last_safe_policy_then_passes(client, db_session):
    from app.models.remediation import LastSafePolicy
    db_session.query(LastSafePolicy).delete()
    db_session.commit()

    drill_before = client.post(
        "/api/v1/recovery/drill",
        json={"policy_version": "policy-current", "simulate": True},
    )
    assert drill_before.status_code == 200
    assert drill_before.json()["passed"] is False

    register = client.post("/api/v1/recovery/last-safe-policy/policy-safe-v1")
    assert register.status_code == 200

    drill_after = client.post(
        "/api/v1/recovery/drill",
        json={"policy_version": "policy-current", "simulate": True},
    )
    assert drill_after.status_code == 200
    assert drill_after.json()["passed"] is True
    assert drill_after.json()["rollback_target"] == "policy-safe-v1"
