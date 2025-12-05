import pytest

from app.db.model import SimulationResult
from app.db.types import EntityType

from .utils import (
    PROJECT_ID,
    USER_SUB_ID_1,
    add_all_db,
    assert_request,
    check_authorization,
    check_creation_fields,
    check_entity_delete_one,
    check_entity_update_one,
    check_missing,
    check_pagination,
)

ROUTE = "simulation-result"
ADMIN_ROUTE = "/admin/simulation-result"


@pytest.fixture
def json_data(simulation_result_json_data):
    return simulation_result_json_data


@pytest.fixture
def public_json_data(public_simulation_result_json_data):
    return public_simulation_result_json_data


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


def test_update_one(clients, public_json_data):
    check_entity_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=public_json_data,
        patch_payload={
            "name": "name",
            "description": "description",
        },
        optional_payload=None,
    )


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_user_read_one(client, model, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)


def test_admin_read_one(client_admin, model, json_data):
    data = assert_request(client_admin.get, url=f"/admin/{ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)


def test_read_many(client, model, json_data):
    data = assert_request(client.get, url=f"{ROUTE}").json()["data"]

    # circuit and root circuit
    assert len(data) == 1

    assert data[0]["id"] == str(model.id)
    _assert_read_response(data[0], json_data)


def test_delete_one(db, clients, public_json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=public_json_data,
        expected_counts_before={
            SimulationResult: 1,
        },
        expected_counts_after={
            SimulationResult: 0,
        },
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, public_json_data):
    # using root_circuit_json_data to avoid the implication of creating two circuits
    # because of the root_circuit_id in circuit_json_data which messes up the check assumptions
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, public_json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


@pytest.fixture
def models(db, json_data, person_id):
    objs = [
        SimulationResult(
            **json_data
            | {
                "name": f"s-{i}",
                "created_by_id": person_id,
                "updated_by_id": person_id,
                "authorized_project_id": PROJECT_ID,
            }
        )
        for i in range(3)
    ]
    return add_all_db(db, objs)


def test_filtering(client, models):
    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    data = req({"created_by__sub_id": USER_SUB_ID_1, "updated_by__sub_id": USER_SUB_ID_1})
    assert len(data) == len(models)

    data = req({"ilike_search": "*description*"})
    assert len(data) == len(models)

    data = req({"ilike_search": "s-1"})
    assert len(data) == 1
