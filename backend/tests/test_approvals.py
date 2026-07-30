def test_list_approvals_manager(client, manager_token):
    response = client.get(
        "/approvals/",
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_approvals_unauthorized_user(client, user_token):
    response = client.get(
        "/approvals/",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403
