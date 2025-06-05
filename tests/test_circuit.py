from app.db.types import EntityType

from .utils import assert_request, check_creation_fields

ROUTE = "circuit"


def _assert_read_response(data, json_data):
    assert "id" in data
    assert "authorized_public" in data
    assert "authorized_project_id" in data
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

    data = assert_request(client.get, url=f"{ROUTE}/{data['id']}").json()
    _assert_read_response(data, circuit_json_data)
