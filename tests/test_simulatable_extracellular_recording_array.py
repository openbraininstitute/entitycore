import pytest

from app.db.model import SimulatableExtracellularRecordingArray
from app.db.types import ElectrodeType, EntityType
from app.routers.types import EntityRoute

from .utils import (
    PROJECT_ID,
    USER_SUB_ID_1,
    add_all_db,
    add_db,
    assert_request,
    check_authorization,
    check_entity_delete_one,
    check_entity_read_many,
    check_entity_read_response,
    check_entity_update_one,
    check_missing,
    check_pagination,
)

ROUTE = f"/{EntityRoute.simulatable_extracellular_recording_array}"
ADMIN_ROUTE = f"/admin/{EntityRoute.simulatable_extracellular_recording_array}"


@pytest.fixture
def json_data(root_circuit):
    return {
        "name": "my-array",
        "description": "my-description",
        "electrode_type": ElectrodeType.custom,
        "circuit_id": str(root_circuit.id),
    }


@pytest.fixture
def public_json_data(public_root_circuit):
    return {
        "name": "my-array",
        "description": "my-description",
        "electrode_type": ElectrodeType.custom,
        "circuit_id": str(public_root_circuit.id),
    }


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


@pytest.fixture
def model(db, person_id, json_data):
    return add_db(
        db,
        SimulatableExtracellularRecordingArray(
            **json_data
            | {
                "created_by_id": person_id,
                "updated_by_id": person_id,
                "authorized_public": False,
                "authorized_project_id": PROJECT_ID,
            },
        ),
    )


def _assert_read_response(data, json_data):
    check_entity_read_response(
        data, json_data, EntityType.simulatable_extracellular_recording_array
    )

    assert data["circuit_id"] == json_data["circuit_id"]
    assert data["electrode_type"] == json_data["electrode_type"]


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
    data = assert_request(client_admin.get, url=f"{ADMIN_ROUTE}/{model.id}").json()
    _assert_read_response(data, json_data)


def test_read_many_1(client, model, json_data):
    data = assert_request(client.get, url=f"{ROUTE}").json()["data"]

    # circuit and root circuit
    assert len(data) == 1

    assert data[0]["id"] == str(model.id)
    _assert_read_response(data[0], json_data)


def test_read_many_2(clients, public_json_data):
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
            SimulatableExtracellularRecordingArray: 1,
        },
        expected_counts_after={
            SimulatableExtracellularRecordingArray: 0,
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
        SimulatableExtracellularRecordingArray(
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


def test_filtering(client, models, root_circuit):
    def req(query):
        return assert_request(client.get, url=ROUTE, params=query).json()["data"]

    data = req({"created_by__sub_id": USER_SUB_ID_1, "updated_by__sub_id": USER_SUB_ID_1})
    assert len(data) == len(models)

    data = req({"ilike_search": "*description*"})
    assert len(data) == len(models)

    data = req({"ilike_search": "s-1"})
    assert len(data) == 1

    data = req({"electrode_type": ElectrodeType.custom})
    assert len(data) == len(models)

    data = req({"circuit_id": str(root_circuit.id)})
    assert len(data) == len(models)
