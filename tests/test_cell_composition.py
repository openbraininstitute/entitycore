import pytest

from app.db.model import CellComposition
from app.db.types import EntityType

from .utils import (
    PROJECT_ID,
    USER_SUB_ID_1,
    add_db,
    assert_request,
    check_entity_delete_one,
    check_entity_read_many,
    check_entity_read_response,
)

ROUTE = "cell-composition"
ADMIN_ROUTE = "/admin/cell-composition"


@pytest.fixture
def json_data(brain_region_id, species_id):
    return {
        "name": "my-composition",
        "description": "my-composition",
        "brain_region_id": str(brain_region_id),
        "species_id": str(species_id),
    }


@pytest.fixture
def cell_composition_id(db, json_data, person_id):
    row = add_db(
        db,
        CellComposition(
            **json_data
            | {
                "created_by_id": person_id,
                "updated_by_id": person_id,
                "authorized_project_id": PROJECT_ID,
            }
        ),
    )
    return row.id


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def _assert_read_response(data, json_data):
    check_entity_read_response(data, json_data, EntityType.cell_composition)


def test_read_one(client, client_admin, cell_composition_id):
    data = assert_request(client.get, url=f"{ROUTE}/{cell_composition_id}").json()
    assert data["name"] == "my-composition"
    assert "assets" in data
    assert data["type"] == EntityType.cell_composition

    data = assert_request(client.get, url=f"{ROUTE}").json()["data"][0]
    assert data["name"] == "my-composition"
    assert "assets" in data
    assert data["type"] == EntityType.cell_composition

    data = assert_request(client_admin.get, url=f"{ADMIN_ROUTE}/{cell_composition_id}").json()
    assert data["name"] == "my-composition"
    assert "assets" in data
    assert data["type"] == EntityType.cell_composition


def test_read_many(clients, json_data):
    check_entity_read_many(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
    )


def test_filtering(client, db, brain_region_id, species_id, person_id):
    row1 = add_db(
        db,
        CellComposition(
            name="my-composition-1",
            description="my-description-1",
            brain_region_id=brain_region_id,
            species_id=species_id,
            created_by_id=person_id,
            updated_by_id=person_id,
            authorized_project_id=PROJECT_ID,
        ),
    )
    add_db(
        db,
        CellComposition(
            name="my-composition-2",
            description="my-description-2",
            brain_region_id=brain_region_id,
            species_id=species_id,
            created_by_id=person_id,
            updated_by_id=person_id,
            authorized_project_id=PROJECT_ID,
        ),
    )
    data = assert_request(client.get, url=f"{ROUTE}", params={"name": "my-composition-1"}).json()[
        "data"
    ]
    assert len(data) == 1
    assert data[0]["name"] == "my-composition-1"
    assert data[0]["id"] == str(row1.id)
    assert "assets" in data[0]
    assert data[0]["type"] == EntityType.cell_composition

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"created_by__sub_id": USER_SUB_ID_1, "updated_by__sub_id": USER_SUB_ID_1},
    ).json()["data"]
    assert len(data) == 2

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"ilike_search": "*description*"},
    ).json()["data"]
    assert len(data) == 2

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"ilike_search": "*composition-1"},
    ).json()["data"]
    assert len(data) == 1


def test_delete_one(db, clients, json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        expected_counts_before={
            CellComposition: 1,
        },
        expected_counts_after={
            CellComposition: 0,
        },
    )
