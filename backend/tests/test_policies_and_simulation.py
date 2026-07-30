import pytest

def test_get_policies(client, user_token):
    response = client.get(
        "/policies/",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_policy_admin(client, admin_token):
    policy_data = {
        "name": "Test Delete Protection Policy",
        "description": "Block large deletes",
        "action": "delete_records",
        "condition_type": "record_count_gt",
        "condition_value": "50",
        "decision": "block",
        "severity": "HIGH",
        "enabled": True,
        "requires_approval": False
    }
    response = client.post(
        "/policies/",
        json=policy_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["name"] == "Test Delete Protection Policy"
    assert res_json["action"] == "delete_records"

def test_create_policy_forbidden_user(client, user_token):
    policy_data = {
        "name": "Unauthorized Policy",
        "action": "delete_records",
        "condition_type": "record_count_gt",
        "condition_value": "50",
        "decision": "block"
    }
    response = client.post(
        "/policies/",
        json=policy_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403

def test_policy_conflicts(client):
    response = client.get("/policies/conflicts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_simulation(client, user_token):
    sim_data = {
        "action": "delete_records",
        "record_count": 500,
        "external": True,
        "classification": "confidential"
    }
    response = client.post(
        "/simulate/",
        json=sim_data,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "simulation_id" in data
    assert "decision" in data
    assert "risk_score" in data
