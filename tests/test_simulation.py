import pytest

from app.db.model import Simulation, SimulationCampaign
from app.db.types import EntityType

from .utils import (
    PROJECT_ID,
    add_all_db,
    assert_request,
    check_authorization,
    check_creation_fields,
    check_missing,
    check_pagination,
    count_db_class,
)

ROUTE = "simulation"
ADMIN_ROUTE = "/admin/simulation"
MODEL = Simulation


@pytest.fixture
def json_data(simulation_json_data):
    return simulation_json_data


@pytest.fixture
def model(simulation):
    return simulation


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
    assert data["type"] == EntityType.simulation

    check_creation_fields(data)


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_update_one(client, client_admin, model):
    new_name = "my_new_name"
    new_description = "my_new_description"

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

    # set scan_parameters
    data = assert_request(
        client.patch,
        url=f"{ROUTE}/{model.id}",
        json={
            "scan_parameters": {"param1": "value1", "param2": "value2"},
        },
    ).json()
    assert data["scan_parameters"]["param1"] == "value1"
    assert data["scan_parameters"]["param2"] == "value2"

    # only admin client can hit admin endpoint
    data = assert_request(
        client.patch,
        url=f"{ADMIN_ROUTE}/{model.id}",
        json={
            "name": "admin_test_name",
            "description": "admin_test_description",
        },
        expected_status_code=403,
    ).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    data = assert_request(
        client_admin.patch,
        url=f"{ADMIN_ROUTE}/{model.id}",
        json={
            "name": "admin_test_name",
            "description": "admin_test_description",
        },
    ).json()

    assert data["name"] == "admin_test_name"
    assert data["description"] == "admin_test_description"

    # admin is treated as regular user for regular route (no authorized project ids)
    data = assert_request(
        client_admin.patch,
        url=f"{ROUTE}/{model.id}",
        json={
            "name": "admin_test",
        },
        expected_status_code=404,
    ).json()
    assert data["error_code"] == "ENTITY_NOT_FOUND"


def test_update_one__public(client, client_admin, json_data):
    # make private entity public
    data = assert_request(
        client.post,
        url=ROUTE,
        json=json_data
        | {
            "authorized_public": True,
        },
    ).json()

    entity_id = data["id"]

    # should not be allowed to update it once public
    data = assert_request(
        client.patch,
        url=f"{ROUTE}/{entity_id}",
        json={"name": "foo"},
        expected_status_code=404,
    ).json()
    assert data["error_code"] == "ENTITY_NOT_FOUND"

    # admin has no such restrictions
    data = assert_request(
        client_admin.patch,
        url=f"{ADMIN_ROUTE}/{entity_id}",
        json={
            "authorized_public": False,
            "name": "foo",
        },
    ).json()
    assert data["authorized_public"] is False
    assert data["name"] == "foo"


def test_read_one(client, client_admin, model, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=f"{ROUTE}").json()["data"]
    assert len(data) == 1
    _assert_read_response(data[0], json_data)

    data = assert_request(client_admin.get, url=f"{ADMIN_ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)


def test_delete_one(db, client, client_admin, model):
    model_id = model.id

    assert count_db_class(db, Simulation) == 1
    assert count_db_class(db, SimulationCampaign) == 1

    data = assert_request(
        client.delete, url=f"{ADMIN_ROUTE}/{model_id}", expected_status_code=403
    ).json()
    assert data["error_code"] == "NOT_AUTHORIZED"
    assert data["message"] == "Service admin role required"

    data = assert_request(client_admin.delete, url=f"{ADMIN_ROUTE}/{model_id}").json()
    assert data["id"] == str(model_id)

    assert count_db_class(db, Simulation) == 0
    assert count_db_class(db, SimulationCampaign) == 1


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
                    "name": f"circuit-{i}",
                    "description": f"circuit-description-{i}",
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


def test_filtering(client, models, simulation_campaign, circuit):
    data = assert_request(
        client.get, url=ROUTE, params={"simulation_campaign_id": str(simulation_campaign.id)}
    ).json()["data"]
    assert len(data) == len(models)

    data = assert_request(client.get, url=ROUTE, params={"entity_id": str(circuit.id)}).json()[
        "data"
    ]
    assert len(data) == len(models)
