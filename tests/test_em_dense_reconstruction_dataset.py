import pytest

from app.db.model import EMDenseReconstructionDataset
from app.db.types import EntityType

from .utils import (
    PROJECT_ID,
    USER_SUB_ID_1,
    add_all_db,
    assert_request,
    check_creation_fields,
    check_missing,
    check_pagination,
    count_db_class,
)

ROUTE = "/em-dense-reconstruction-dataset"
ADMIN_ROUTE = f"/admin{ROUTE}"
MODEL = EMDenseReconstructionDataset


@pytest.fixture
def json_data(em_dense_reconstruction_dataset_json_data):
    return em_dense_reconstruction_dataset_json_data


@pytest.fixture
def model(em_dense_reconstruction_dataset):
    return em_dense_reconstruction_dataset


@pytest.fixture
def create_id(client_admin_with_project, json_data):
    def _create_id(**kwargs):
        return assert_request(
            client_admin_with_project.post, url=ROUTE, json=json_data | kwargs
        ).json()["id"]

    return _create_id


def _assert_read_response(data, json_data):
    assert "id" in data
    assert "authorized_public" in data
    assert "authorized_project_id" in data
    assert "assets" in data
    assert data["type"] == EntityType.em_dense_reconstruction_dataset
    assert data["name"] == json_data["name"]
    check_creation_fields(data)


def test_create_one(client, client_admin, client_admin_with_project, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data, expected_status_code=403).json()
    assert data["message"] == "Service admin role required"

    data = assert_request(
        client_admin.post, url=ROUTE, json=json_data, expected_status_code=403
    ).json()
    assert data["message"] == "The headers virtual-lab-id and project-id are required"

    data = assert_request(client_admin_with_project.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_read_one(client, model, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=f"{ROUTE}").json()["data"]
    assert len(data) == 1
    _assert_read_response(data[0], json_data)


def test_read_many(clients, json_data):

    route = ROUTE
    admin_route = ADMIN_ROUTE

    model_id = assert_request(clients.admin_with_project.post, url=route, json=json_data).json()[
        "id"
    ]

    def _req(client, client_route):
        data = assert_request(client.get, url=client_route).json()["data"]
        assert len(data) == 1
        assert data[0]["id"] == str(model_id)
        _assert_read_response(data[0], json_data)

    # user that created the resource can read it
    _req(clients.user_1, route)

    # but cannot use the admin endpoint
    data = assert_request(
        clients.user_1.get,
        url=admin_route,
        expected_status_code=403,
    ).json()
    assert data["message"] == "Service admin role required"

    # but cannot use the admin endpoint
    data = assert_request(
        clients.user_2.get,
        url=admin_route,
        expected_status_code=403,
    ).json()
    assert data["message"] == "Service admin role required"

    # service admins can only read from admin route (not global resource)
    _req(clients.admin, admin_route)


def test_missing(client):
    check_missing(ROUTE, client)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


@pytest.fixture
def models(db, json_data, person_id):
    db_models = [
        MODEL(
            **(
                json_data
                | {
                    "name": f"name-{i}",
                    "description": f"description-{i}",
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
    params = {"name__ilike": "name-"}
    data = assert_request(client.get, url=ROUTE, params=params).json()["data"]
    assert len(data) == len(models)

    params = {"name__ilike": "unknown"}
    data = assert_request(client.get, url=ROUTE, params=params).json()["data"]
    assert len(data) == 0

    params = {"name": "name-0", "with_facets": True}
    response = assert_request(client.get, url=ROUTE, params=params).json()
    data = response["data"]
    facets = response["facets"]
    assert len(data) == 1
    assert data[0]["name"] == "name-0"
    assert facets == {
        "brain_region": [
            {
                "count": 1,
                "id": brain_region_id,
                "label": "RedRegion",
                "type": "brain_region",
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
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"created_by__sub_id": USER_SUB_ID_1, "updated_by__sub_id": USER_SUB_ID_1},
    ).json()["data"]

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"ilike_search": "*description*"},
    ).json()["data"]
    assert len(data) == len(models)

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"ilike_search": "name-1"},
    ).json()["data"]
    assert len(data) == 1


def test_delete_one(db, clients, json_data):

    route = ROUTE
    admin_route = ADMIN_ROUTE
    expected_counts_before = {
        EMDenseReconstructionDataset: 1,
    }
    expected_counts_after = {
        EMDenseReconstructionDataset: 0,
    }

    def _req_count(client, client_route, model_id):
        for db_class, count in expected_counts_before.items():
            assert count_db_class(db, db_class) == count

        data = assert_request(client.delete, url=f"{client_route}/{model_id}").json()
        assert data["id"] == str(model_id)

        for db_class, count in expected_counts_after.items():
            assert count_db_class(db, db_class) == count

    model_id = assert_request(clients.admin_with_project.post, url=route, json=json_data).json()[
        "id"
    ]

    # user cannot use regular or admin delete routes
    data = assert_request(
        clients.user_1.delete, url=f"{route}/{model_id}", expected_status_code=403
    ).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    data = assert_request(
        clients.user_1.delete, url=f"{route}/{model_id}", expected_status_code=403
    ).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    _req_count(clients.admin, admin_route, model_id)


def test_update_one(clients, json_data):

    route = ROUTE
    admin_route = ADMIN_ROUTE
    patch_payload = {"name": "foo"}

    def _patch_compare(method, url, patch_data):
        data = assert_request(method, url=url, json=patch_data).json()
        for key, value in patch_data.items():
            assert data[key] == value, f"Key: {key} Expected: {value} Actual: {data[key]}"

    data = assert_request(clients.admin_with_project.post, url=route, json=json_data).json()
    model_id = data["id"]

    old_values = {k: data[k] for k in patch_payload}

    # global resource update endpoint requires admin client
    data = assert_request(
        clients.user_1.patch,
        url=f"{route}/{model_id}",
        json=patch_payload,
        expected_status_code=403,
    ).json()
    assert data["message"] == "Service admin role required"

    # update using admin client and regular route
    _patch_compare(clients.admin.patch, f"{route}/{model_id}", patch_payload)

    # revert
    _patch_compare(clients.admin.patch, f"{route}/{model_id}", old_values)

    # global resource admin endpoint requires admin client
    data = assert_request(
        clients.user_1.patch,
        url=f"{admin_route}/{model_id}",
        json=patch_payload,
        expected_status_code=403,
    ).json()
    assert data["message"] == "Service admin role required"

    # update using admin client and admin route
    _patch_compare(clients.admin.patch, f"{admin_route}/{model_id}", patch_payload)

    # revert
    _patch_compare(clients.admin.patch, f"{admin_route}/{model_id}", old_values)
