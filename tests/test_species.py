import pytest

from app.db.model import Species

from .utils import check_creation_fields
from tests.utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    assert_request,
    check_global_read_one,
    check_global_update_one,
    count_db_class,
)

ROUTE = "/species"
ADMIN_ROUTE = "/admin/species"


@pytest.fixture
def json_data():
    return {
        "name": "my-species",
        "taxonomy_id": "NCBITaxon:1000",
    }


def _assert_read_response(data, json_data):
    assert "id" in data
    assert data["name"] == json_data["name"]
    assert data["taxonomy_id"] == json_data["taxonomy_id"]
    assert "created_by" in data
    assert "updated_by" in data


def test_create_species(client, client_admin):
    count = 3
    items = []
    for i in range(count):
        name = f"Test Species {i}"
        taxonomy_id = f"12345_{i}"
        response = client_admin.post(ROUTE, json={"name": name, "taxonomy_id": taxonomy_id})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == name
        assert data["taxonomy_id"] == taxonomy_id
        check_creation_fields(data)
        assert "id" in data
        items.append(data)

    response = client.get(f"{ROUTE}/{items[0]['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data == items[0]
    check_creation_fields(data)

    response = client.get(ROUTE)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == count
    assert data == items
    check_creation_fields(data[0])

    # test filter
    response = client.get(ROUTE, params={"name": "Test Species 1"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data == [items[1]]
    check_creation_fields(data[0])

    # test semantic_search
    response = client.get(ROUTE, params={"semantic_search": "speeecies"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 3  # semantic search just reorders - it does not filter out


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
            "name": "my-new-species",
            "taxonomy_id": "NCBITaxon:9000",
        },
    )


def test_delete_one(db, client, client_admin, species_id):
    model_id = species_id

    assert count_db_class(db, Species) == 1

    data = assert_request(
        client.delete, url=f"{ADMIN_ROUTE}/{model_id}", expected_status_code=403
    ).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    data = assert_request(client_admin.delete, url=f"{ADMIN_ROUTE}/{model_id}").json()
    assert data["id"] == str(model_id)

    assert count_db_class(db, Species) == 0


def test_missing(client):
    response = client.get(f"{ROUTE}/{MISSING_ID}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/{MISSING_ID_COMPACT}")
    assert response.status_code == 404

    response = client.get(f"{ROUTE}/42424242")
    assert response.status_code == 422

    response = client.get(f"{ROUTE}/notanumber")
    assert response.status_code == 422
