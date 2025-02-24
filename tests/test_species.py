ROUTE = "/species/"


def test_create_species(client):
    name = "Test Species"
    response = client.post(ROUTE, json={"name": name, "taxonomy_id": "12345"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Species"
    assert data["taxonomy_id"] == "12345"
    assert "id" in data
    id_ = data["id"]

    response = client.get(f"{ROUTE}{id_}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == id_
    assert data["name"] == name
    assert data["taxonomy_id"] == "12345"

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == name
    assert data[0]["id"] == id_


def test_missing_role(client):
    response = client.get(f"{ROUTE}42424242")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}notanumber")
    assert response.status_code == 422
