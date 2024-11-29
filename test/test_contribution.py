
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