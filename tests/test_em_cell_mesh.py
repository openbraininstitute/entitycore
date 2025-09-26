import pytest

from app.db.model import EMCellMesh
from app.db.types import EntityType

from .utils import (
    PROJECT_ID,
    add_all_db,
    assert_request,
    check_authorization,
    check_creation_fields,
    check_entity_delete_one,
    check_missing,
    check_pagination,
)

ROUTE = "/em-cell-mesh"
ADMIN_ROUTE = "/admin/em-cell-mesh"
MODEL = EMCellMesh


@pytest.fixture
def json_data(em_cell_mesh_json_data):
    return em_cell_mesh_json_data


@pytest.fixture
def model(em_cell_mesh):
    return em_cell_mesh


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


def _assert_read_response(data, json_data):
    assert "id" in data
    assert "authorized_public" in data
    assert "authorized_project_id" in data
    assert "assets" in data
    assert data["type"] == EntityType.em_cell_mesh
    assert data["em_dense_reconstruction_dataset"] == {
        "id": json_data["em_dense_reconstruction_dataset_id"],
        "type": EntityType.em_dense_reconstruction_dataset,
    }
    check_creation_fields(data)


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_read_one(client, model, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=f"{ROUTE}").json()["data"]
    assert len(data) == 1
    _assert_read_response(data[0], json_data)


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, json_data):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


@pytest.fixture
def models(db, json_data, person_id):
    db_models = [
        MODEL(
            **(
                json_data
                | {
                    "level_of_detail": i,
                    "dense_reconstruction_cell_id": i,
                    "mesh_type": ["static", "dynamic"][i % 2],
                    "created_by_id": person_id,
                    "updated_by_id": person_id,
                    "authorized_project_id": PROJECT_ID,
                }
            )
        )
        for i in range(4)
    ]

    add_all_db(db, db_models)

    return db_models


def test_filtering(client, models, brain_region_id, species_id, strain_id):
    params = {"em_dense_reconstruction_dataset__name__ilike": "microns"}
    data = assert_request(client.get, url=ROUTE, params=params).json()["data"]
    assert len(data) == len(models)

    params = {"em_dense_reconstruction_dataset__name__ilike": "unknown"}
    data = assert_request(client.get, url=ROUTE, params=params).json()["data"]
    assert len(data) == 0

    params = {"level_of_detail": 0, "with_facets": True}
    response = assert_request(client.get, url=ROUTE, params=params).json()
    data = response["data"]
    facets = response["facets"]
    assert len(data) == 1
    assert data[0]["level_of_detail"] == 0
    assert facets == {
        "brain_region": [
            {
                "count": 1,
                "id": brain_region_id,
                "label": "RedRegion",
                "type": "brain_region",
            },
        ],
        "em_dense_reconstruction_dataset": [
            {
                "count": 1,
                "id": str(models[0].em_dense_reconstruction_dataset_id),
                "label": "MICrONS",
                "type": "em_dense_reconstruction_dataset",
            },
        ],
        "species": [
            {
                "count": 1,
                "id": species_id,
                "label": "Test Species",
                "type": "subject.species",
            },
        ],
        "strain": [
            {
                "count": 1,
                "id": strain_id,
                "label": "Test Strain",
                "type": "subject.strain",
            },
        ],
    }


def test_delete_one(db, clients, json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=json_data,
        expected_counts_before={
            EMCellMesh: 1,
        },
        expected_counts_after={
            EMCellMesh: 0,
        },
    )
