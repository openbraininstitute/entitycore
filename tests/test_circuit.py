import pytest

from app.db.model import Circuit
from app.db.types import CircuitBuildCategory, CircuitScale, EntityType

from .utils import (
    PROJECT_ID,
    add_all_db,
    assert_request,
    check_authorization,
    check_creation_fields,
    check_missing,
    check_pagination,
)

ROUTE = "circuit"


@pytest.fixture
def create_id(client, root_circuit_json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=root_circuit_json_data | kwargs).json()[
            "id"
        ]

    return _create_id


def _assert_read_response(data, json_data):
    assert "id" in data
    assert "authorized_public" in data
    assert "authorized_project_id" in data
    assert "assets" in data
    assert data["name"] == json_data["name"]
    assert data["description"] == json_data["description"]
    assert data["subject"]["id"] == json_data["subject_id"]
    assert data["license"]["id"] == json_data["license_id"]
    assert data["root_circuit_id"] == json_data["root_circuit_id"]
    assert data["atlas_id"] == json_data["atlas_id"]
    assert data["type"] == EntityType.circuit
    assert data["has_morphologies"] == json_data["has_morphologies"]
    assert data["has_point_neurons"] == json_data["has_point_neurons"]
    assert data["has_electrical_cell_models"] == json_data["has_electrical_cell_models"]
    assert data["has_spines"] == json_data["has_spines"]
    assert data["build_category"] == json_data["build_category"]
    assert data["scale"] == json_data["scale"]

    check_creation_fields(data)


def test_create_one(client, circuit_json_data):
    data = assert_request(client.post, url=ROUTE, json=circuit_json_data).json()
    _assert_read_response(data, circuit_json_data)


def test_read_one(client, circuit, circuit_json_data):
    data = assert_request(client.get, url=f"{ROUTE}/{circuit.id}").json()
    _assert_read_response(data, circuit_json_data)


def test_read_many(client, circuit, circuit_json_data):
    data = assert_request(client.get, url=f"{ROUTE}").json()["data"]

    # circuit and root circuit
    assert len(data) == 2

    circuit_data = next(d for d in data if d["id"] == str(circuit.id))
    _assert_read_response(circuit_data, circuit_json_data)


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(client_user_1, client_user_2, client_no_project, root_circuit_json_data):
    # using root_circuit_json_data to avoid the implication of creating two circuits
    # because of the root_circuit_id in circuit_json_data which messes up the check assumptions
    check_authorization(
        ROUTE, client_user_1, client_user_2, client_no_project, root_circuit_json_data
    )


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


@pytest.fixture
def models(db, circuit_json_data, person_id):
    booleans = [True, False, True, False, True, False]

    scales = [
        CircuitScale.single,
        CircuitScale.microcircuit,
        CircuitScale.whole_brain,
        CircuitScale.single,
        CircuitScale.microcircuit,
        CircuitScale.whole_brain,
    ]
    categories = [
        CircuitBuildCategory.computational_model,
        CircuitBuildCategory.em_reconstruction,
        CircuitBuildCategory.computational_model,
        CircuitBuildCategory.em_reconstruction,
        CircuitBuildCategory.computational_model,
        CircuitBuildCategory.em_reconstruction,
    ]

    db_circuits = [
        Circuit(
            **(
                circuit_json_data
                | {
                    "name": f"circuit-{i}",
                    "description": f"circuit-description-{i}",
                    "has_morphologies": bool_value,
                    "has_point_neurons": bool_value,
                    "has_electrical_cell_models": bool_value,
                    "has_spines": bool_value,
                    "number_neurons": 10 * i + 1,
                    "number_synapses": 1000 * i + 1,
                    "number_connections": 100 * i + 1,
                    "scale": scale,
                    "build_category": category,
                    "created_by_id": person_id,
                    "updated_by_id": person_id,
                    "authorized_project_id": PROJECT_ID,
                }
            )
        )
        for i, (bool_value, scale, category) in enumerate(
            zip(booleans, scales, categories, strict=False)
        )
    ]

    add_all_db(db, db_circuits)

    return db_circuits


def test_filtering(client, root_circuit, models):
    data = assert_request(
        client.get, url=ROUTE, params={"root_circuit_id": str(root_circuit.id)}
    ).json()["data"]
    assert len(data) == len(models)

    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "root_circuit_id": str(root_circuit.id),
            "has_morphologies": True,
        },
    ).json()["data"]
    assert len(data) == 3

    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "root_circuit_id": str(root_circuit.id),
            "has_morphologies": True,
            "has_point_neurons": False,
        },
    ).json()["data"]
    assert len(data) == 0

    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "root_circuit_id": str(root_circuit.id),
            "build_category": "computational_model",
            "number_neurons__lte": 11,
        },
    ).json()["data"]
    assert len(data) == 1

    data = assert_request(
        client.get,
        url=ROUTE,
        params={
            "root_circuit_id": str(root_circuit.id),
            "scale__in": "single,whole_brain",
        },
    ).json()["data"]
    assert len(data) == 4
