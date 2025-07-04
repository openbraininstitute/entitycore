import pytest

from app.db.model import Simulation
from app.db.types import EntityType

from .utils import (
    PROJECT_ID,
    add_all_db,
    assert_request,
    check_authorization,
    check_creation_fields,
    check_missing,
    check_pagination,
)

ROUTE = "simulation"
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
