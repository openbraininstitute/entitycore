def test_create_organization(client):
    label = "test_organization label"
    alternative_name = "test organization alternative name"
    response = client.post(
        "/organization/",
        json={"pref_label": label, "alternative_name": alternative_name},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pref_label"] == label
    assert data["alternative_name"] == alternative_name
    assert "id" in data
    id_ = data["id"]
    response = client.get(f"/organization/{id_}")
    assert response.status_code == 200
    data = response.json()
    assert data["pref_label"] == label
    assert data["alternative_name"] == alternative_name
    assert data["id"] == id_
    response = client.get("/organization/")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["id"] == id_
    assert len(data) == 1


def test_missing_organization(client):
    response = client.get("/organization/42424242")
    assert response.status_code == 404

    response = client.get("/organization/notanumber")
    assert response.status_code == 422
