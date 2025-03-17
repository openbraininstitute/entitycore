from tests.utils import MISSING_ID, MISSING_ID_COMPACT

ROUTE = "/role"


def test_create_role(client):
    name = "important role"
    role_id = "important role id"
    response = client.post(ROUTE, json={"name": name, "role_id": role_id})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == name
    assert data["role_id"] == role_id
    assert "id" in data
    id_ = data["id"]

    response = client.get(f"{ROUTE}/{id_}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == id_
    assert data["name"] == name
    assert data["role_id"] == role_id

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == name
    assert data[0]["id"] == id_


def test_missing(client):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422
