import pytest

from app.db.model import Simulation, SimulationCampaign
from app.db.types import EntityType

from .utils import (
    PROJECT_ID,
    add_all_db,
    add_db,
    assert_request,
    check_authorization,
    check_creation_fields,
    check_missing,
    check_pagination,
)

ROUTE = "simulation-campaign"
MODEL = SimulationCampaign


@pytest.fixture
def json_data(simulation_campaign_json_data):
    return simulation_campaign_json_data


@pytest.fixture
def model(simulation_campaign):
    return simulation_campaign


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
    assert data["type"] == EntityType.simulation_campaign
    assert "simulations" in data

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
def models(db, json_data, person_id, simulation_json_data, circuit):
    db_campaigns = [
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

    add_all_db(db, db_campaigns)

    # create 1 simulation with the same name for the first three campaigns
    for i in range(3):
        add_db(
            db,
            Simulation(
                **simulation_json_data
                | {
                    "simulation_campaign_id": db_campaigns[i].id,
                    "entity_id": circuit.id,
                    "created_by_id": person_id,
                    "updated_by_id": person_id,
                    "authorized_project_id": PROJECT_ID,
                }
            ),
        )

    return db_campaigns


def test_filtering(client, models, simulation_json_data, person_id):
    data = assert_request(client.get, url=ROUTE, params={"created_by__id": str(person_id)}).json()[
        "data"
    ]
    assert len(data) == len(models) + 1  # +1 campaign from simulation_json_data fixture

    data = assert_request(
        client.get, url=ROUTE, params={"simulation__name": simulation_json_data["name"]}
    ).json()["data"]
    assert len(data) == 3
