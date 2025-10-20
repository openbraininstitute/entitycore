import pytest

from app.db.model import Circuit, CircuitBuildCategory, CircuitScale, Simulation, SimulationCampaign
from app.db.types import EntityType

from .utils import (
    PROJECT_ID,
    add_all_db,
    add_db,
    assert_request,
    check_authorization,
    check_creation_fields,
    check_entity_delete_one,
    check_missing,
    check_pagination,
)

ROUTE = "simulation-campaign"
ADMIN_ROUTE = "/admin/simulation-campaign"
MODEL = SimulationCampaign


@pytest.fixture
def json_data(simulation_campaign_json_data):
    return simulation_campaign_json_data


@pytest.fixture
def public_json_data(public_simulation_campaign_json_data):
    return public_simulation_campaign_json_data


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
    assert data["scan_parameters"] == json_data["scan_parameters"]

    check_creation_fields(data)


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_read_one(client, client_admin, model, json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=f"{ROUTE}").json()["data"]
    assert len(data) == 1
    _assert_read_response(data[0], json_data)

    data = assert_request(client_admin.get, url=f"{ADMIN_ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)


def test_delete_one(db, clients, public_json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=public_json_data,
        expected_counts_before={
            SimulationCampaign: 1,
        },
        expected_counts_after={
            SimulationCampaign: 0,
        },
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, public_json_data):
    check_authorization(ROUTE, client_user_1, client_user_2, client_no_project, public_json_data)


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


@pytest.fixture
def multiple_circuits(db, brain_atlas_id, subject_id, brain_region_id, license_id, person_id):
    circuits_data = [
        {
            "name": "micro-circuit-1",
            "description": "Micro Circuit 1",
            "has_morphologies": True,
            "has_point_neurons": False,
            "has_electrical_cell_models": True,
            "has_spines": False,
            "number_neurons": 100,
            "number_synapses": 1000,
            "number_connections": 50,
            "scale": CircuitScale.microcircuit,
            "build_category": CircuitBuildCategory.computational_model,
            "atlas_id": brain_atlas_id,
            "subject_id": subject_id,
            "brain_region_id": brain_region_id,
            "license_id": license_id,
            "authorized_public": False,
            "created_by_id": person_id,
            "updated_by_id": person_id,
            "authorized_project_id": PROJECT_ID,
        },
        {
            "name": "micro-circuit-2",
            "description": "Micro Circuit 2",
            "has_morphologies": False,
            "has_point_neurons": True,
            "has_electrical_cell_models": False,
            "has_spines": True,
            "number_neurons": 1000,
            "number_synapses": 10000,
            "number_connections": 200,
            "scale": CircuitScale.microcircuit,
            "build_category": CircuitBuildCategory.em_reconstruction,
            "atlas_id": brain_atlas_id,
            "subject_id": subject_id,
            "brain_region_id": brain_region_id,
            "license_id": license_id,
            "authorized_public": False,
            "created_by_id": person_id,
            "updated_by_id": person_id,
            "authorized_project_id": PROJECT_ID,
        },
        {
            "name": "pair-circuit-1",
            "description": "Pair Circuit 1",
            "has_morphologies": True,
            "has_point_neurons": True,
            "has_electrical_cell_models": True,
            "has_spines": True,
            "number_neurons": 10000,
            "number_synapses": 100000,
            "number_connections": 500,
            "scale": CircuitScale.pair,
            "build_category": CircuitBuildCategory.computational_model,
            "atlas_id": brain_atlas_id,
            "subject_id": subject_id,
            "brain_region_id": brain_region_id,
            "license_id": license_id,
            "authorized_public": False,
            "created_by_id": person_id,
            "updated_by_id": person_id,
            "authorized_project_id": PROJECT_ID,
        },
    ]

    circuits = [add_db(db, Circuit(**circuit_data)) for circuit_data in circuits_data]
    return circuits


@pytest.fixture
def campaigns_with_different_circuits(
    db, json_data, person_id, simulation_json_data, multiple_circuits
):
    campaigns = []

    for i, circuit in enumerate(multiple_circuits):
        campaign = add_db(
            db,
            MODEL(
                **(
                    json_data
                    | {
                        "entity_id": str(circuit.id),
                        "name": f"campaign-circuit-{i}",
                        "description": f"Campaign for circuit {i}",
                        "created_by_id": person_id,
                        "updated_by_id": person_id,
                        "authorized_project_id": PROJECT_ID,
                    }
                )
            ),
        )
        campaigns.append(campaign)

        add_db(
            db,
            Simulation(
                **simulation_json_data
                | {
                    "name": f"simulation-circuit-{i}",
                    "simulation_campaign_id": campaign.id,
                    "entity_id": circuit.id,
                    "created_by_id": person_id,
                    "updated_by_id": person_id,
                    "authorized_project_id": PROJECT_ID,
                }
            ),
        )

    return campaigns


def test_filter_by_circuit_id(client, campaigns_with_different_circuits, multiple_circuits):  # noqa: ARG001
    first_circuit_id = str(multiple_circuits[0].id)

    data = assert_request(client.get, url=ROUTE, params={"entity_id": first_circuit_id}).json()[
        "data"
    ]
    assert len(data) == 1
    assert data[0]["name"] == "campaign-circuit-0"

    data = assert_request(client.get, url=ROUTE, params={"simulation__circuit__id": first_circuit_id}).json()[
        "data"
    ]

    assert len(data) == 1
    assert data[0]["name"] == "campaign-circuit-0"

    second_circuit_id = str(multiple_circuits[1].id)
    data = assert_request(client.get, url=ROUTE, params={"simulation__circuit__id": second_circuit_id}).json()[
        "data"
    ]

    assert len(data) == 1
    assert data[0]["name"] == "campaign-circuit-1"


def test_filter_by_circuit_name(client, campaigns_with_different_circuits, multiple_circuits):  # noqa: ARG001
    data = assert_request(
        client.get, url=ROUTE, params={"simulation__circuit__name": "micro-circuit-1"}
    ).json()["data"]

    assert len(data) == 1
    assert data[0]["name"] == "campaign-circuit-0"

    data = assert_request(
        client.get, url=ROUTE, params={"simulation__circuit__name__in": "micro-circuit-2"}
    ).json()["data"]

    assert len(data) == 1
    assert data[0]["name"] == "campaign-circuit-1"


def test_filter_by_circuit_scale(client, campaigns_with_different_circuits, multiple_circuits):  # noqa: ARG001
    data = assert_request(
        client.get, url=ROUTE, params={"simulation__circuit__scale": CircuitScale.microcircuit}
    ).json()["data"]

    assert len(data) == 2

    data = assert_request(
        client.get, url=ROUTE, params={"simulation__circuit__scale": CircuitScale.pair}
    ).json()["data"]

    assert len(data) == 1


def test_filter_by_circuit_scale_empty(
    client,
    campaigns_with_different_circuits,  # noqa: ARG001
    multiple_circuits,  # noqa: ARG001
):
    data = assert_request(
        client.get, url=ROUTE, params={"simulation__circuit__scale": CircuitScale.small}
    ).json()["data"]

    assert len(data) == 0


def test_filter_by_circuit_scale_in(client, campaigns_with_different_circuits, multiple_circuits):  # noqa: ARG001
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"simulation__circuit__scale__in": [CircuitScale.microcircuit, CircuitScale.pair]},
    ).json()["data"]

    assert len(data) == 3
    campaign_names = {campaign["name"] for campaign in data}
    assert campaign_names == {"campaign-circuit-0", "campaign-circuit-1", "campaign-circuit-2"}


def test_filter_by_circuit_build_category(
    client,
    campaigns_with_different_circuits,  # noqa: ARG001
    multiple_circuits,  # noqa: ARG001
):
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"simulation__circuit__build_category": CircuitBuildCategory.computational_model},
    ).json()["data"]

    assert len(data) == 2
    campaign_names = {campaign["name"] for campaign in data}
    assert campaign_names == {"campaign-circuit-0", "campaign-circuit-2"}

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"simulation__circuit__build_category": CircuitBuildCategory.em_reconstruction},
    ).json()["data"]

    assert len(data) == 1
    assert data[0]["name"] == "campaign-circuit-1"


def test_filter_by_circuit_build_category_in(
    client,
    campaigns_with_different_circuits,  # noqa: ARG001
    multiple_circuits,  # noqa: ARG001
):
    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "simulation__circuit__build_category__in": [
                CircuitBuildCategory.computational_model,
                CircuitBuildCategory.em_reconstruction,
            ],
        },
    ).json()["data"]

    assert len(data) == 3
    campaign_names = {campaign["name"] for campaign in data}
    assert campaign_names == {"campaign-circuit-0", "campaign-circuit-1", "campaign-circuit-2"}
