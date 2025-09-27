import pytest

from app.db.model import Strain

from tests.utils import (
    MISSING_ID,
    MISSING_ID_COMPACT,
    check_creation_fields,
    check_global_delete_one,
    check_global_read_one,
    check_global_update_one,
)

ROUTE = "/strain"
ADMIN_ROUTE = "/admin/strain"


@pytest.fixture
def json_data(species_id):
    return {
        "name": "strain",
        "taxonomy_id": "NCBITaxon:2000",
        "species_id": str(species_id),
    }


def _assert_read_response(data, json_data):
    assert "id" in data
    assert data["name"] == json_data["name"]
    assert data["taxonomy_id"] == json_data["taxonomy_id"]
    assert "created_by" in data
    assert "updated_by" in data


def test_create_strain(client, client_admin, species_id, person_id):
    count = 3
    items = []
    for i in range(count):
        name = f"Test Strain {i}"
        taxonomy_id = f"TaxonomyID_{i}"
        response = client_admin.post(
            ROUTE,
            json={
                "name": name,
                "taxonomy_id": taxonomy_id,
                "species_id": species_id,
                "created_by_id": str(person_id),
                "updated_by_id": str(person_id),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["taxonomy_id"] == taxonomy_id
        assert data["species_id"] == species_id
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
    response = client.get(ROUTE, params={"name": "Test Strain 1"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data == [items[1]]
    check_creation_fields(data[0])

    # test pagination
    response = client.get(ROUTE, params={"page": 1, "page_size": 2})
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    assert data == [items[0], items[1]]

    # test pagination (page validation error)
    response = client.get(ROUTE, params={"page": 0, "page_size": 2})
    assert response.status_code == 422
    assert response.json() == {
        "details": [
            {
                "ctx": {
                    "ge": 1,
                },
                "loc": [
                    "query",
                    "page",
                ],
                "msg": "Input should be greater than or equal to 1",
                "type": "greater_than_equal",
            },
        ],
        "error_code": "INVALID_REQUEST",
        "message": "Validation error",
    }

    # test semantic_search
    response = client.get(ROUTE, params={"semantic_search": "straaains"})
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
            "name": "new-strain",
            "taxonomy_id": "NCBITaxon:9000",
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
            Strain: 1,
        },
        expected_counts_after={
            Strain: 0,
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
