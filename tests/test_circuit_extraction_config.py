import pytest

from app.db.model import Circuit, CircuitExtractionConfig
from app.db.types import EntityType

from .utils import (
    assert_request,
    check_authorization,
    check_entity_delete_one,
    check_entity_read_response,
    check_missing,
    check_pagination,
)

ROUTE = "circuit-extraction-config"
ADMIN_ROUTE = "/admin/circuit-extraction-config"
MODEL = CircuitExtractionConfig


@pytest.fixture
def json_data(circuit_extraction_config_json_data):
    return circuit_extraction_config_json_data


@pytest.fixture
def public_json_data(json_data):
    return json_data | {"authorized_public": True}


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


@pytest.fixture
def model_id(circuit_extraction_config_id):
    return circuit_extraction_config_id


def _assert_read_response(data, json_data):
    check_entity_read_response(data, json_data, EntityType.circuit_extraction_config)
    assert data["circuit_id"]
    assert data["scan_parameters"] == json_data["scan_parameters"]


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)


def test_read_one(clients, model_id, json_data):
    data = assert_request(clients.user_1.get, url=f"{ROUTE}/{model_id}").json()
    _assert_read_response(data, json_data)

    data = assert_request(clients.user_1.get, url=f"{ROUTE}").json()["data"]
    assert len(data) == 1
    _assert_read_response(data[0], json_data)

    data = assert_request(clients.admin.get, url=f"{ADMIN_ROUTE}/{model_id}").json()
    _assert_read_response(data, json_data)


def test_delete_one(db, clients, public_json_data):
    check_entity_delete_one(
        db=db,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        clients=clients,
        json_data=public_json_data,
        expected_counts_before={
            CircuitExtractionConfig: 1,
            Circuit: 1,
        },
        expected_counts_after={
            CircuitExtractionConfig: 0,
            Circuit: 1,
        },
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_authorization(clients, public_json_data):
    check_authorization(ROUTE, clients.user_1, clients.user_2, clients.no_project, public_json_data)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


@pytest.fixture
def models(create_id):
    return [create_id(name=f"config-{i}") for i in range(3)]


def test_filtering_ordering(client, models, root_circuit):
    root_circuit_id = str(root_circuit.id)

    def _req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    data = _req({})
    assert len(data) == len(models)

    data = _req({"name__ilike": "config"})
    assert len(data) == len(models)

    data = _req({"name": "config-0"})
    assert len(data) == 1
    assert data[0]["name"] == "config-0"

    data = _req({"circuit_id": root_circuit_id})
    assert len(data) == len(models)

    data = _req({"circuit_id__in": [root_circuit_id]})
    assert len(data) == len(models)

    data = _req({"circuit__id": [root_circuit_id]})
    assert len(data) == len(models)

    data = _req({"order_by": "-name"})
    assert [d["name"] for d in data] == ["config-2", "config-1", "config-0"]

    data = _req({"order_by": "-name", "name__in": ["config-1", "config-2"]})
    assert [d["name"] for d in data] == ["config-2", "config-1"]
