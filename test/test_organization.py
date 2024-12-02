def test_create_organization(client):
    name = "test_organization"
    label = "test_organization label"
    alternative_name = "test organization alternative name"
    response = client.post(
        "/organization/", json={"name": name, "label": label, "alternative_name": alternative_name}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == name 
    assert data["label"] == label
    assert data["alternative_name"] == alternative_name
    assert "id" in data
    id_ = data["id"]
    response = client.get(f"/organization/{id_}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == name 
    assert data["label"] == label
    assert data["alternative_name"] == alternative_name
    assert data["id"] == id_
    response = client.get("/organization/")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["name"] == name
    assert data[0]["id"] == id_
    assert len(data) == 1
