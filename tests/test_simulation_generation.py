from datetime import UTC, datetime

import pytest
import sqlalchemy as sa
from pydantic import TypeAdapter

from app.db.model import Generation, SimulationGeneration, Usage
from app.db.types import ActivityType

from .utils import (
    PROJECT_ID,
    assert_request,
    check_creation_fields,
    check_missing,
    check_pagination,
    create_cell_morphology_id,
)

DateTimeAdapter = TypeAdapter(datetime)

ROUTE = "simulation-generation"
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


def test_create_one(client, json_data):
    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=f"{ROUTE}/{data['id']}").json()
    _assert_read_response(data, json_data)

    data = assert_request(client.get, url=ROUTE).json()["data"][0]
    _assert_read_response(data, json_data)


def test_create_one__empty_ids(client, json_data):
    json_data = {k: v for k, v in json_data.items() if k not in {"used_ids", "generated_ids"}}

    data = assert_request(client.post, url=ROUTE, json=json_data).json()
    _assert_read_response(data, json_data, empty_ids=True)

    data = assert_request(client.get, url=f"{ROUTE}/{data['id']}").json()
    _assert_read_response(data, json_data, empty_ids=True)

    data = assert_request(client.get, url=ROUTE).json()["data"][0]
    _assert_read_response(data, json_data, empty_ids=True)


def test_create_one__unauthorized_entities(
    client_user_1,
    client_user_2,
    json_data,
    species_id,
    brain_region_id,
):
    """Do not allow associations with entities that are not authorized to the user."""

    user1_morph_id = create_cell_morphology_id(
        client_user_1,
        species_id=species_id,
        strain_id=None,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )
    user2_morph_id = create_cell_morphology_id(
        client_user_2,
        species_id=species_id,
        strain_id=None,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )
    user2_public_morph_id = create_cell_morphology_id(
        client_user_2,
        species_id=species_id,
        strain_id=None,
        brain_region_id=brain_region_id,
        authorized_public=True,
    )

    # user1 is forbidden to create Usage association with entity created by user2
    unauthorized_used = json_data | {
        "used_ids": [str(user2_morph_id)],
        "generated_ids": [str(user1_morph_id)],
    }
    assert_request(client_user_1.post, url=ROUTE, json=unauthorized_used, expected_status_code=404)

    # user1 is forbidden to create Generation association with entity created by user2
    unauthorized_used = json_data | {
        "used_ids": [str(user1_morph_id)],
        "generated_ids": [str(user2_morph_id)],
    }
    assert_request(client_user_1.post, url=ROUTE, json=unauthorized_used, expected_status_code=404)

    # user1 is forbidden to create both associations with entities created by user 2
    unauthorized_used = json_data | {
        "used_ids": [str(user2_morph_id)],
        "generated_ids": [str(user2_morph_id)],
    }
    assert_request(client_user_1.post, url=ROUTE, json=unauthorized_used, expected_status_code=404)

    # user 1 is allowed to create Usage with public entity created by user2
    authorized_used = json_data | {
        "used_ids": [str(user2_public_morph_id)],
        "generated_ids": [str(user1_morph_id)],
    }
    assert_request(client_user_1.post, url=ROUTE, json=authorized_used, expected_status_code=200)

    # user 1 is allowed to create Generation with public entity created by user2
    authorized_used = json_data | {
        "used_ids": [str(user1_morph_id)],
        "generated_ids": [str(user2_public_morph_id)],
    }
    assert_request(client_user_1.post, url=ROUTE, json=authorized_used, expected_status_code=200)

    # user 1 is allowed to create both with public entity created by user2
    authorized_used = json_data | {
        "used_ids": [str(user2_public_morph_id)],
        "generated_ids": [str(user2_public_morph_id)],
    }
    assert_request(client_user_1.post, url=ROUTE, json=authorized_used, expected_status_code=200)


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


def test_delete_one(db, client, models):
    # sanity check
    assert _count_associations(db, models[1]) == 2
    assert _count_associations(db, models[3]) == 4

    data = assert_request(client.delete, url=f"{ROUTE}/{models[1]}").json()
    assert data["id"] == str(models[1])
    assert _is_deleted(db, data["id"])

    assert _count_associations(db, models[1]) == 0
    assert _count_associations(db, models[3]) == 4

    data = assert_request(client.delete, url=f"{ROUTE}/{models[3]}").json()
    assert data["id"] == str(models[3])
    assert _is_deleted(db, data["id"])

    assert _count_associations(db, models[1]) == 0
    assert _count_associations(db, models[3]) == 0

    data = assert_request(client.get, url=f"{ROUTE}").json()["data"]
    assert {d["id"] for d in data} == {str(models[0]), str(models[2]), str(models[4])}


def _count_associations(db, activity_id):
    n_usages = db.execute(
        sa.select(sa.func.count(Usage.usage_activity_id)).where(
            Usage.usage_activity_id == activity_id
        )
    ).scalar()
    n_generations = db.execute(
        sa.select(sa.func.count(Generation.generation_activity_id)).where(
            Generation.generation_activity_id == activity_id
        )
    ).scalar()

    return n_usages + n_generations


def _is_deleted(db, model_id):
    return db.get(MODEL, model_id) is None


def test_update_one(client, root_circuit, simulation_result, create_id):
    gen1 = create_id(
        used_ids=[str(root_circuit.id)],
        generated_ids=[],
    )

    end_time = datetime.now(UTC)

    update_json = {
        "end_time": str(end_time),
        "generated_ids": [str(simulation_result.id)],
    }

    data = assert_request(client.patch, url=f"{ROUTE}/{gen1}", json=update_json).json()
    assert DateTimeAdapter.validate_python(data["end_time"]) == end_time
    assert len(data["generated"]) == 1
    assert data["generated"][0]["id"] == str(simulation_result.id)


def test_update_one__fail_if_generated_ids_unauthorized(
    client_user_1, client_user_2, json_data, species_id, brain_region_id
):
    """Test that it is not allowed to update generated_ids with unauthorized entities."""

    user1_morph_id = create_cell_morphology_id(
        client_user_1,
        species_id=species_id,
        strain_id=None,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )
    user2_morph_id = create_cell_morphology_id(
        client_user_2,
        species_id=species_id,
        strain_id=None,
        brain_region_id=brain_region_id,
        authorized_public=False,
    )

    json_data |= {
        "used_ids": [str(user1_morph_id)],
        "generated_ids": [],
    }

    data = assert_request(client_user_1.post, url=ROUTE, json=json_data).json()

    update_json = {
        "generated_ids": [str(user2_morph_id)],
    }
    data = assert_request(
        client_user_1.patch, url=f"{ROUTE}/{data['id']}", json=update_json, expected_status_code=404
    ).json()
    assert data["details"] == f"Cannot access entities {user2_morph_id}"


def test_update_one__fail_if_generated_ids_exists(
    client, root_circuit, simulation_result, create_id
):
    """Test activity Generation associations cannot be updated if they already exist."""
    gen1 = create_id(
        used_ids=[str(root_circuit.id)],
        generated_ids=[str(root_circuit.id)],
    )
    update_json = {
        "generated_ids": [str(simulation_result.id)],
    }
    data = assert_request(
        client.patch, url=f"{ROUTE}/{gen1}", json=update_json, expected_status_code=404
    ).json()
    assert data["details"] == "It is forbidden to update generated_ids if they exist."
