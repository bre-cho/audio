def test_decisions_create_update_and_list(client):
    create = client.post(
        "/api/v1/decisions",
        json={
            "trigger_type": "canary_failure",
            "scenarios_considered": [{"name": "s1", "risk": 70, "confidence": 40}],
            "selected_action": "rollback",
            "rejected_actions": ["promote"],
            "score_breakdown": {"safety": 95, "latency": 80},
            "selected_reason": "safety first",
            "confidence_score": 88,
            "policy_version": "policy-v1",
            "decision_actor": "system",
        },
    )
    assert create.status_code == 200
    decision_id = create.json()["decision_id"]

    update = client.patch(
        f"/api/v1/decisions/{decision_id}",
        json={"execution_status": "executed", "actual_json": {"result": "ok"}},
    )
    assert update.status_code == 200
    assert update.json()["execution_status"] == "executed"

    listed = client.get("/api/v1/decisions")
    assert listed.status_code == 200
    assert any(row["decision_id"] == decision_id for row in listed.json())


def test_decisions_simulate_what_if(client):
    response = client.post(
        "/api/v1/decisions/simulate",
        json={
            "scenarios": [
                {"risk": 85, "confidence": 20},
                {"risk": 70, "confidence": 30},
            ],
            "candidate_actions": ["rollback", "fallback", "promote"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["selected_action"] in {"rollback", "fallback", "promote"}
    assert set(body["action_scores"].keys()) == {"rollback", "fallback", "promote"}
