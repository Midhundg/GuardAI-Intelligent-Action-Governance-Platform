import pytest

def test_analytics_dashboard_endpoints(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    dash = client.get("/analytics/dashboard", headers=headers)
    assert dash.status_code == 200

    daily = client.get("/analytics/daily-requests", headers=headers)
    assert daily.status_code == 200

    blocked = client.get("/analytics/blocked-actions", headers=headers)
    assert blocked.status_code == 200

    approval_rate = client.get("/analytics/approval-success-rate", headers=headers)
    assert approval_rate.status_code == 200

    avg_lat = client.get("/analytics/average-latency", headers=headers)
    assert avg_lat.status_code == 200

    agent = client.get("/analytics/most-used-agent", headers=headers)
    assert agent.status_code == 200

    policy = client.get("/analytics/most-used-policy", headers=headers)
    assert policy.status_code == 200

def test_recommendations(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/recommendations/", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_audit_export_csv(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    res = client.get("/audit/export/csv", headers=headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "ID,Request ID,Timestamp" in res.text

def test_prometheus_metrics(client):
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "process_cpu_seconds_total" in res.text or "python_info" in res.text or "http" in res.text
