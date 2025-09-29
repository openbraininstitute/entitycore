from datetime import UTC, datetime

import pytest
from pydantic import TypeAdapter

from app.db.model import CellMorphology, EModel, Generation, SimulationGeneration, Usage
from app.db.types import ActivityType

from .utils import (
    PROJECT_ID,
    assert_request,
    check_activity_create_one__unauthorized_entities,
    check_activity_delete_one,
    check_activity_update_one,
    check_activity_update_one__fail_if_generated_ids_exists,
    check_activity_update_one__fail_if_generated_ids_unauthorized,
    check_creation_fields,
    check_missing,
    check_pagination,
    create_cell_morphology_id,
)

DateTimeAdapter = TypeAdapter(datetime)

ROUTE = "simulation-generation"
ADMIN_ROUTE = "/admin/simulation-generation"
MODEL = SimulationGeneration


@pytest.fixture
def json_data(morphology_id, emodel_id):
    return {
        "start_time": str(datetime.now(UTC)),
        "end_time": str(datetime.now(UTC)),
        "used_ids": [str(morphology_id)],
        "generated_ids": [str(emodel_id)],
    }


@pytest.fixture
def create_id(client, json_data):
    def _create_id(**kwargs):
        return assert_request(client.post, url=ROUTE, json=json_data | kwargs).json()["id"]

    return _create_id


def _assert_read_response(data, json_data, *, empty_ids=False):
    assert "id" in data

    if empty_ids:
        assert len(data["used"]) == 0
        assert len(data["generated"]) == 0
    else:
        assert data["used"] == [
            {
                "id": json_data["used_ids"][0],
                "type": "cell_morphology",
                "authorized_project_id": PROJECT_ID,
                "authorized_public": False,
            }
        ]
        assert data["generated"] == [
            {
                "id": json_data["generated_ids"][0],
                "type": "emodel",
                "authorized_project_id": PROJECT_ID,
                "authorized_public": False,
            }
        ]
    check_creation_fields(data)
    assert DateTimeAdapter.validate_python(data["start_time"]) == DateTimeAdapter.validate_python(
        json_data["start_time"]
    )
    assert DateTimeAdapter.validate_python(data["end_time"]) == DateTimeAdapter.validate_python(
        json_data["end_time"]
    )
    assert data["type"] == ActivityType.simulation_generation.value


def test_create_one(client, client_admin, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=f"{ROUTE}/{data['id']}").json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=ROUTE).json()["data"][0]
    _assert_read_response(data, json_data)

    data = assert_request(client_admin.get, url=f"{ADMIN_ROUTE}/{data['id']}").json()
    _assert_read_response(data, json_data)


def test_create_one__empty_ids(client, client_admin, json_data):
    json_data = {k: v for k, v in json_data.items() if k not in {"used_ids", "generated_ids"}}

    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data, empty_ids=True)

    data = assert_request(client.get, url=f"{ROUTE}/{data['id']}").json()
    _assert_read_response(data, json_data, empty_ids=True)

    data = assert_request(client.get, url=ROUTE).json()["data"][0]
    _assert_read_response(data, json_data, empty_ids=True)

    data = assert_request(client_admin.get, url=f"{ADMIN_ROUTE}/{data['id']}").json()
    _assert_read_response(data, json_data, empty_ids=True)


def test_create_one__unauthorized_entities(
    db,
    client_user_1,
    client_user_2,
    json_data,
    subject_id,
    brain_region_id,
):
    """Do not allow associations with entities that are not authorized to the user."""

    user1_morph_id = create_cell_morphology_id(
        client_user_1,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )
    user2_morph_id = create_cell_morphology_id(
        client_user_2,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )
    user2_public_morph_id = create_cell_morphology_id(
        client_user_2,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        authorized_public=True,
    )
    check_activity_create_one__unauthorized_entities(
        db=db,
        route=ROUTE,
        client_user_1=client_user_1,
        json_data=json_data,
        u1_private_entity_id=user1_morph_id,
        u2_private_entity_id=user2_morph_id,
        u2_public_entity_id=user2_public_morph_id,
    )


def test_missing(client):
    check_missing(ROUTE, client)


def test_pagination(client, create_id):
    check_pagination(ROUTE, client, create_id)


@pytest.fixture
def models(morphology_id, root_circuit, simulation_result, create_id):
    return [
        create_id(
            used_ids=[str(root_circuit.id)],
            generated_ids=[],
        ),
        create_id(
            used_ids=[str(root_circuit.id)],
            generated_ids=[str(root_circuit.id)],
        ),
        create_id(
            used_ids=[str(root_circuit.id)],
            generated_ids=[str(simulation_result.id)],
        ),
        create_id(
            used_ids=[str(root_circuit.id), str(simulation_result.id)],
            generated_ids=[str(root_circuit.id), str(simulation_result.id)],
        ),
        create_id(
            used_ids=[str(morphology_id), str(root_circuit.id)],
            generated_ids=[str(simulation_result.id)],
        ),
    ]


def test_filtering(client, models, root_circuit, simulation_result):
    data = assert_request(client.get, url=ROUTE).json()["data"]
    assert len(data) == len(models)

    data = assert_request(client.get, url=ROUTE, params={"used__id": str(root_circuit.id)}).json()[
        "data"
    ]
    assert len(data) == 5

    data = assert_request(
        client.get, url=ROUTE, params={"generated__id": str(root_circuit.id)}
    ).json()["data"]
    assert len(data) == 2

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"used__id": str(root_circuit.id), "generated__id": str(root_circuit.id)},
    ).json()["data"]
    assert len(data) == 2

    # backwards compat
    data = assert_request(
        client.get, url=ROUTE, params={"used__id__in": f"{root_circuit.id},{simulation_result.id}"}
    ).json()["data"]
    assert len(data) == 5

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"used__id__in": [str(root_circuit.id), str(simulation_result.id)]},
    ).json()["data"]
    assert len(data) == 5

    # backwards compat
    data = assert_request(
        client.get,
        url=ROUTE,
        params={"generated__id__in": f"{root_circuit.id},{simulation_result.id}"},
    ).json()["data"]
    assert len(data) == 4

    data = assert_request(
        client.get,
        url=ROUTE,
        params={"generated__id__in": [str(root_circuit.id), str(simulation_result.id)]},
    ).json()["data"]
    assert len(data) == 4


def test_delete_one(db, clients, json_data):
    check_activity_delete_one(
        db=db,
        clients=clients,
        json_data=json_data,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        expected_counts_before={
            CellMorphology: 1,
            EModel: 1,
            Usage: 1,
            Generation: 1,
            SimulationGeneration: 1,
        },
        expected_counts_after={
            CellMorphology: 1,
            EModel: 1,
            Usage: 0,
            Generation: 0,
            SimulationGeneration: 0,
        },
    )


def test_update_one(client, client_admin, root_circuit, simulation_result, create_id):
    check_activity_update_one(
        client=client,
        client_admin=client_admin,
        route=ROUTE,
        admin_route=ADMIN_ROUTE,
        used_id=root_circuit.id,
        generated_id=simulation_result.id,
        constructor_func=create_id,
    )


def test_update_one__fail_if_generated_ids_unauthorized(
    db, client_user_1, client_user_2, json_data, subject_id, brain_region_id
):
    """Test that it is not allowed to update generated_ids with unauthorized entities."""

    user1_morph_id = create_cell_morphology_id(
        client_user_1,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )
    user2_morph_id = create_cell_morphology_id(
        client_user_2,
        subject_id=subject_id,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )
    check_activity_update_one__fail_if_generated_ids_unauthorized(
        db=db,
        route=ROUTE,
        client_user_1=client_user_1,
        json_data=json_data,
        u1_private_entity_id=user1_morph_id,
        u2_private_entity_id=user2_morph_id,
    )


def test_update_one__fail_if_generated_ids_exists(
    client, root_circuit, simulation_result, create_id
):
    """Test activity Generation associations cannot be updated if they already exist."""
    check_activity_update_one__fail_if_generated_ids_exists(
        client=client,
        route=ROUTE,
        entity_id_1=root_circuit.id,
        entity_id_2=simulation_result.id,
        constructor_func=create_id,
    )
