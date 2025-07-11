from app.db.model import Role

from tests.utils import MISSING_ID, MISSING_ID_COMPACT, assert_request, count_db_class

ROUTE = "/role"


def test_create_role(client, client_admin):
    name = "important role"
    role_id = "important role id"
    response = client_admin.post(ROUTE, json={"name": name, "role_id": role_id})
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


def test_delete_one(db, client, client_admin):
    response = client_admin.post(ROUTE, json={"name": "foo", "role_id": "bar"})
    assert response.status_code == 200
    data = response.json()

    model_id = data["id"]

    assert count_db_class(db, Role) == 1

    data = assert_request(client.delete, url=f"{ROUTE}/{model_id}", expected_status_code=403).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    data = assert_request(client_admin.delete, url=f"{ROUTE}/{model_id}").json()
    assert data["id"] == str(model_id)

    assert count_db_class(db, Role) == 0


def test_missing(client):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422
