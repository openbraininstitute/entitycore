
def test_create_contribution(client):
    response = client.post(
        "/person/", json={"first_name": "jd", "last_name": "courcol"}
    )
    assert response.status_code == 200
    data = response.json()
    person_id = data["id"]
    response = client.post(
        "/contribution/",
        json={
            "agent_id": person_id,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["agent"]["id"] == person_id
    contribution_id = data["id"]
    response = client.get(f"/contribution/{contribution_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["agent"]["id"] == person_id
    assert data["agent"]["first_name"] == "jd"
    assert data["agent"]["last_name"] == "courcol"
    assert data["creation_date"] is not None
    assert data["update_date"] is not None
    assert data["id"] == contribution_id