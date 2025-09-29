import pytest

from app.db.model import License

from tests.utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    assert_request,
    check_global_delete_one,
    check_global_read_one,
)

ROUTE = "/license"
ADMIN_ROUTE = "/admin/license"


@pytest.fixture
def json_data():
    return {
        "name": "Test License",
        "description": "a license description",
        "label": "a label",
    }


def _assert_read_response(data, json_data):
    assert "id" in data
    assert data["name"] == json_data["name"]
    assert data["label"] == json_data["label"]
    assert data["description"] == json_data["description"]
    assert "creation_date" in data
    assert "update_date" in data


def test_create_license(client, client_admin):
    response = client_admin.post(
        ROUTE,
        json={
            "name": "Test License",
            "description": "a license description",
            "label": "a label",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test License"
    assert "id" in data
    assert data["description"] == "a license description"
    id_ = data["id"]

    response = client.get(f"{ROUTE}/{id_}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test License"
    assert data["description"] == "a license description"

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "Test License"
    assert data[0]["description"] == "a license description"


def test_read_one(clients, json_data):
    check_global_read_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        validator=_assert_read_response,
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


def test_delete_one(db, clients, json_data):
    check_global_delete_one(
        db=db,
        clients=clients,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        json_data=json_data,
        expected_counts_before={
            License: 1,
        },
        expected_counts_after={
            License: 0,
        },
    )


def test_filtering(clients, json_data):
    assert_request(clients.admin.post, url=ROUTE, json=json_data | {"name": "n1", "label": "l"})
    assert_request(clients.admin.post, url=ROUTE, json=json_data | {"name": "n2", "label": "l"})

    data = assert_request(clients.user_1.get, url=ROUTE, params={"name": "n1"}).json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "n1"

    data = assert_request(clients.user_1.get, url=ROUTE, params={"label": "l"}).json()["data"]
    assert len(data) == 2
    assert data[0]["label"] == "l"
    assert data[1]["label"] == "l"
