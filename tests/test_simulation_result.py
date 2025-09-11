import pytest

from app.db.model import SimulationResult
from app.db.types import EntityType

from .utils import (
    assert_request,
    check_authorization,
    check_creation_fields,
    check_missing,
    check_pagination,
    count_db_class,
)

ROUTE = "simulation-result"
ADMIN_ROUTE = "/admin/simulation-result"


@pytest.fixture
def json_data(simulation_result_json_data):
    return simulation_result_json_data


@pytest.fixture
def model(simulation_result):
    return simulation_result


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
    assert data["name"] == json_data["name"]
    assert data["description"] == json_data["description"]
    assert data["type"] == EntityType.simulation_result
    assert data["simulation_id"] is not None

    check_creation_fields(data)


def test_update_one(client, model):
    new_name = "my_new_simulation_result_name"
    new_description = "my_new_simulation_result_description"

    data = assert_request(
        client.patch,
        url=f"{ROUTE}/{model.id}",
        json={
            "name": new_name,
            "description": new_description,
        },
    ).json()

    assert data["name"] == new_name
    assert data["description"] == new_description


def test_update_one__public(client, json_data):
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data
        | {
            "authorized_public": True,
        },
    ).json()

    # should not be allowed to update it once public
    data = assert_request(
        client.patch,
        url=f"{ROUTE}/{data['id']}",
        json={"name": "foo"},
        expected_status_code=404,
    ).json()
    assert data["error_code"] == "ENTITY_NOT_FOUND"


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_read_one(client, model, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)


def test_read_many(client, model, json_data):
    data = assert_request(client.get, url=f"{ROUTE}").json()["data"]

    # circuit and root circuit
    assert len(data) == 1

    assert data[0]["id"] == str(model.id)
    _assert_read_response(data[0], json_data)


def test_delete_one(db, client, client_admin, model):
    model_id = model.id

    assert count_db_class(db, SimulationResult) == 1

    data = assert_request(
        client.delete, url=f"{ADMIN_ROUTE}/{model_id}", expected_status_code=403
    ).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    data = assert_request(client_admin.delete, url=f"{ADMIN_ROUTE}/{model_id}").json()
    assert data["id"] == str(model_id)

    assert count_db_class(db, SimulationResult) == 0


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, json_data):
    # using root_circuit_json_data to avoid the implication of creating two circuits
    # because of the root_circuit_id in circuit_json_data which messes up the check assumptions
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)
