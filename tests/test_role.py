import pytest

from app.db.model import Role

from tests.utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    assert_request,
    check_global_delete_one,
    check_global_read_one,
    check_global_update_one,
)

ROUTE = "/role"
ADMIN_ROUTE = "/admin/role"


@pytest.fixture
def json_data():
    return {
        "name": "role",
        "role_id": "role_id",
    }


def _assert_read_response(data, json_data):
    assert "id" in data
    assert data["name"] == json_data["name"]
    assert data["role_id"] == json_data["role_id"]
    assert "creation_date" in data
    assert "update_date" in data


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


def test_read_one(clients, json_data):
    check_global_read_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        validator=_assert_read_response,
    )


def test_update_one(clients, json_data):
    check_global_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        patch_payload={
            "name": "new-name",
            "role_id": "new_role_id",
        },
    )


def test_delete_one(db, clients, json_data):
    check_global_delete_one(
        db=db,
        clients=clients,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        json_data=json_data,
        expected_counts_before={
            Role: 1,
        },
        expected_counts_after={
            Role: 0,
        },
    )


def test_missing(client):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422


def test_filtering(clients):
    assert_request(clients.admin.post, url=ROUTE, json={"name": "r1", "role_id": "role1"})
    assert_request(clients.admin.post, url=ROUTE, json={"name": "r2", "role_id": "role2"})

    data = assert_request(clients.user_1.get, url=ROUTE, params={"name": "r1"}).json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "r1"

    data = assert_request(clients.user_1.get, url=ROUTE, params={"role_id": "role1"}).json()["data"]
    assert len(data) == 1
    assert data[0]["role_id"] == "role1"

    data = assert_request(clients.user_1.get, url=ROUTE, params={"name__ilike": "r"}).json()["data"]
    assert {d["name"] for d in data} == {"r1", "r2"}
