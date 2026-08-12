import pytest

from app.db.model import Simulation, SimulationCampaign
from app.db.types import ElectrodeType, EntityType
from app.types import EntityRoute

from .utils import (
    PROJECT_ID,
    USER_SUB_ID_1,
    add_all_db,
    assert_request,
    check_authorization,
    check_creation_fields,
    check_entity_delete_one,
    check_entity_read_many,
    check_entity_update_one,
    check_missing,
    check_pagination,
)

ROUTE = "simulation"
ADMIN_ROUTE = "/admin/simulation"
MODEL = Simulation


@pytest.fixture
def json_data(simulation_json_data):
    return simulation_json_data


@pytest.fixture
def public_json_data(public_simulation_json_data):
    return public_simulation_json_data


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
    assert "recording_arrays" in data
    assert data["name"] == json_data["name"]
    assert data["description"] == json_data["description"]
    assert data["type"] == EntityType.simulation

    check_creation_fields(data)


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)
    assert data["recording_arrays"] == []


def test_create_one_with_recording_arrays(client, json_data, root_circuit):
    array_route = f"/{EntityRoute.simulatable_extracellular_recording_array}"
    arrays = [
        assert_request(
            client.post,
            url=array_route,
            json={
                "name": f"array-{i}",
                "description": f"array-description-{i}",
                "electrode_type": ElectrodeType.custom,
                "circuit_id": str(root_circuit.id),
            },
        ).json()
        for i in range(2)
    ]
    payload = json_data | {"recording_arrays": [{"id": array["id"]} for array in arrays]}
    data = assert_request(client.post, url=ROUTE, json=payload).json()
    _assert_read_response(data, payload)
    assert {array["id"] for array in data["recording_arrays"]} == {array["id"] for array in arrays}


def test_update_one(clients, public_json_data):
    check_entity_update_one(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=public_json_data,
        patch_payload={
            "name": "name",
            "description": "description",
            "scan_parameters": {"param1": "value1", "param2": "value2"},
        },
        optional_payload=None,
    )


def test_read_one(client, client_admin, model, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=f"{ROUTE}").json()["data"]
    assert len(data) == 1
    _assert_read_response(data[0], json_data)

    data = assert_request(client_admin.get, url=f"{ADMIN_ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)


def test_read_many(clients, public_json_data):
    check_entity_read_many(
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=public_json_data,
    )


def test_delete_one(db, clients, public_json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=public_json_data,
        expected_counts_before={
            Simulation: 1,
            SimulationCampaign: 1,
        },
        expected_counts_after={
            Simulation: 0,
            SimulationCampaign: 1,
        },
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, public_json_data):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, public_json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


@pytest.fixture
def models(db, json_data, user_id):
    db_models = [
        MODEL(
            **(
                json_data
                | {
                    "name": f"circuit-{i}",
                    "description": f"circuit-description-{i}",
                    "created_by_id": user_id,
                    "updated_by_id": user_id,
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

    data = assert_request(
        client.get, url=ROUTE, params={"circuit__id": str(circuit.id), "with_facets": True}
    ).json()["data"]
    assert len(data) == len(models)

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"circuit__build_category": str(circuit.build_category), "with_facets": True},
    ).json()["data"]
    assert len(data) == len(models)

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"circuit__build_category": str(circuit.build_category), "with_facets": True},
    ).json()["data"]
    assert len(data) == len(models)

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"created_by__id": USER_SUB_ID_1, "updated_by__id": USER_SUB_ID_1},
    ).json()["data"]
    assert len(data) == len(models)

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"ilike_search": "*description*"},
    ).json()["data"]
    assert len(data) == len(models)

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"ilike_search": "circuit-1"},
    ).json()["data"]
    assert len(data) == 1

    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "lifecycle_status": "active",
            "simulation_campaign_id": str(simulation_campaign.id),
        },
    ).json()["data"]
    assert len(data) == len(models)
